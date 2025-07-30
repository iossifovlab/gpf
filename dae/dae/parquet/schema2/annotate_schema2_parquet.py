from __future__ import annotations

import argparse
import itertools
import logging
import operator
import os
import pathlib
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime

import yaml

from dae.annotation.annotate_utils import (
    add_input_files_to_task_graph,
    cache_pipeline_resources,
    get_stuff_from_context,
)
from dae.annotation.annotation_config import (
    RawPipelineConfig,
)
from dae.annotation.annotation_factory import (
    adjust_for_reannotation,
    build_annotation_pipeline,
    load_pipeline_from_yaml,
)
from dae.annotation.annotation_pipeline import (
    ReannotationPipeline,
    get_deleted_attributes,
)
from dae.annotation.genomic_context import (
    CLIAnnotationContextProvider,
)
from dae.genomic_resources.cli import VerbosityConfiguration
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.parquet.parquet_writer import (
    append_meta_to_parquet,
    serialize_summary_schema,
)
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.parquet.schema2.loader import ParquetLoader
from dae.parquet.schema2.merge_parquet import merge_variants_parquets
from dae.parquet.schema2.processing_pipeline import (
    AnnotationPipelineVariantsBatchFilter,
    AnnotationPipelineVariantsFilter,
    DeleteAttributesFromVariantFilter,
    DeleteAttributesFromVariantsBatchFilter,
    Schema2SummaryVariantsBatchSource,
    Schema2SummaryVariantsSource,
)
from dae.parquet.schema2.variants_parquet_writer import (
    Schema2SummaryVariantBatchConsumer,
    Schema2SummaryVariantConsumer,
    VariantsParquetWriter,
)
from dae.schema2_storage.schema2_layout import (
    Schema2DatasetLayout,
    create_schema2_dataset_layout,
)
from dae.task_graph.cli_tools import TaskGraphCli
from dae.task_graph.graph import Task, TaskGraph
from dae.utils.processing_pipeline import Filter, PipelineProcessor, Source
from dae.utils.regions import Region, split_into_regions

logger = logging.getLogger("parquet_schema2_annotation")


@dataclass
class _ProcessingArgs:
    work_dir: str
    batch_size: int
    region_size: int
    allow_repeated_attributes: bool
    full_reannotation: bool


def backup_schema2_study(directory: str) -> Schema2DatasetLayout:
    """
    Backup current meta and summary data for a parquet study.

    Renames the meta Parquet file and summary variants directory by
    attaching a suffix with the current date, then returns a corrected
    layout using the newly-renamed paths. This clears the way for then new
    'meta' and 'summary' that will be produced when reannotating a Parquet
    study in place.
    """
    loader = ParquetLoader.load_from_dir(directory)
    assert loader.layout.summary is not None
    meta_path = pathlib.Path(loader.layout.meta)
    summary_path = pathlib.Path(loader.layout.summary)

    date = datetime.today().strftime("%Y%m%d")

    bak_meta_name = f"{meta_path.stem}_{date}"
    bak_summary_name = f"summary_{date}"

    if meta_path.with_stem(bak_meta_name).exists():
        counts = len(list(meta_path.parent.glob(f"{bak_meta_name}*")))
        bak_meta_name = f"{bak_meta_name}-{counts}"

    if summary_path.with_name(bak_summary_name).exists():
        counts = len(list(summary_path.parent.glob(f"{bak_summary_name}*")))
        bak_summary_name = f"{bak_summary_name}-{counts}"

    return Schema2DatasetLayout(
        loader.layout.study,
        loader.layout.pedigree,
        str(summary_path.rename(summary_path.with_name(bak_summary_name))),
        loader.layout.family,
        str(meta_path.rename(meta_path.with_stem(bak_meta_name))),
        loader.layout.base_dir,
    )


def produce_regions(
    target_region: str | None,
    region_size: int,
    contig_lens: dict[str, int],
) -> list[str]:
    """Produce regions to annotate by."""
    regions: list[Region] = []
    for contig, contig_length in contig_lens.items():
        regions.extend(split_into_regions(contig, contig_length, region_size))

    if target_region is not None:
        region_obj = Region.from_str(target_region)
        assert region_obj.start is not None
        assert region_obj.stop is not None
        if region_obj.chrom not in contig_lens:
            raise KeyError(
                f"No such contig '{region_obj.chrom}' found in data!")
        regions = list(filter(None, [region_obj.intersection(reg)
                                     for reg in regions]))

    return list(map(repr, regions))


def produce_schema2_annotation_tasks(  # pylint:disable=R0917
    task_graph: TaskGraph,
    loader: ParquetLoader,
    output_dir: str,
    raw_pipeline: RawPipelineConfig,
    grr: GenomicResourceRepo,
    target_region: str | None,
    args: _ProcessingArgs,
) -> list[Task]:
    """Produce TaskGraph tasks for Parquet file annotation."""

    if "reference_genome" not in loader.meta:
        raise ValueError("No reference genome found in study metadata!")
    genome = ReferenceGenome(
        grr.get_resource(loader.meta["reference_genome"]))

    contig_lens = {}
    contigs = loader.contigs or genome.chromosomes
    for contig in contigs:
        contig_lens[contig] = genome.get_chrom_length(contig)

    regions = produce_regions(target_region, args.region_size, contig_lens)
    tasks = []
    for idx, region in enumerate(regions):
        tasks.append(task_graph.create_task(
            f"part_{region}",
            process_parquet,
            args=[loader.layout, raw_pipeline, grr.definition,
                  output_dir, idx, Region.from_str(region),
                  args],
            deps=[],
        ))
    return tasks


def merge_partitions(
    summary_dir: str,
    partitions: list[list[tuple[str, str]]],
    partition_descriptor: PartitionDescriptor,
) -> None:
    """Helper method to merge Parquet files in partitioned studies."""
    for partition in partitions:
        output_dir = partition_descriptor.partition_directory(
            summary_dir, partition)
        merge_variants_parquets(
            partition_descriptor, output_dir, partition,
            variants_type="summary")


def produce_schema2_merging_tasks(
    task_graph: TaskGraph,
    sync_task: Task,
    reference_genome: ReferenceGenome,
    loader: ParquetLoader,
    output_layout: Schema2DatasetLayout,
) -> list[Task]:
    """Produce TaskGraph tasks for Parquet file merging."""

    if loader.layout.summary is None:
        raise ValueError("No summary variants to merge!")

    partition_descriptor = loader.partition_descriptor
    chromosome_lengths = reference_genome.get_all_chrom_lengths()
    tasks = []
    for region_bin, group in itertools.groupby(
        partition_descriptor.build_summary_partitions(chromosome_lengths),
        operator.attrgetter("region_bin"),
    ):
        partitions = list(group)
        if len(partitions) == 0:
            continue
        tasks.append(task_graph.create_task(
            f"merge_parquet_files_summary_region_bin_{region_bin}",
            merge_partitions,
            args=[output_layout.summary, partitions, partition_descriptor],
            deps=[sync_task],
        ))
    return tasks


def symlink_pedigree_and_family_variants(
    src_layout: Schema2DatasetLayout,
    dest_layout: Schema2DatasetLayout,
) -> None:
    """
    Mirror pedigree and family variants data using symlinks.
    """
    os.symlink(
        pathlib.Path(src_layout.pedigree).parent,
        pathlib.Path(dest_layout.pedigree).parent,
        target_is_directory=True,
    )
    if src_layout.family is not None and dest_layout.family is not None:
        os.symlink(
            src_layout.family,
            dest_layout.family,
            target_is_directory=True,
        )


def write_new_meta(
    loader: ParquetLoader,
    pipeline: ReannotationPipeline,
    output_layout: Schema2DatasetLayout,
) -> None:
    """Produce and write new metadata to the output Parquet dataset."""
    meta_keys = ["annotation_pipeline", "summary_schema"]
    meta_values = [
        yaml.dump(pipeline.raw, sort_keys=False),
        serialize_summary_schema(pipeline.get_attributes(),
                                 loader.partition_descriptor),
    ]
    for k, v in loader.meta.items():
        if k in {"annotation_pipeline", "summary_schema"}:
            continue  # ignore old annotation
        meta_keys.append(k)
        meta_values.append(str(v))
    append_meta_to_parquet(output_layout.meta, meta_keys, meta_values)


def process_parquet(  # pylint:disable=too-many-positional-arguments
    input_layout: Schema2DatasetLayout,
    pipeline_config: RawPipelineConfig,
    grr_definition: dict | None,
    output_dir: str,
    bucket_idx: int,
    region: Region,
    args: _ProcessingArgs,
) -> None:
    """Process a Parquet dataset for annotation."""
    loader = ParquetLoader(input_layout)
    grr = build_genomic_resource_repository(definition=grr_definition)
    variants_blob_serializer = loader.meta.get(
        "variants_blob_serializer",
        "json",
    )

    pipeline = build_annotation_pipeline(
        pipeline_config, grr,
        allow_repeated_attributes=args.allow_repeated_attributes,
        work_dir=pathlib.Path(args.work_dir),
    )

    pipeline_config_old = loader.meta["annotation_pipeline"] \
        if loader.has_annotation else None

    pipeline_previous = None
    if pipeline_config_old is not None:
        pipeline_previous = load_pipeline_from_yaml(pipeline_config_old, grr)

    if pipeline_previous and not args.full_reannotation:
        adjust_for_reannotation(pipeline, pipeline_previous)

    attributes_to_delete = []
    if pipeline_previous:
        attributes_to_delete = get_deleted_attributes(
            pipeline,
            pipeline_previous,
            full_reannotation=args.full_reannotation,
        )

    annotation_attributes = [
        attr for attr in pipeline.get_attributes()
        if not attr.internal
    ]

    writer = VariantsParquetWriter(
        output_dir,
        annotation_attributes,
        loader.partition_descriptor,
        bucket_index=bucket_idx,
        variants_blob_serializer=variants_blob_serializer,
    )

    source: Source
    filters: list[Filter] = []

    if args.batch_size <= 0:
        source = Schema2SummaryVariantsSource(loader)
        filters.extend([
            DeleteAttributesFromVariantFilter(attributes_to_delete),
            AnnotationPipelineVariantsFilter(pipeline),
            Schema2SummaryVariantConsumer(writer),
        ])
    else:
        source = Schema2SummaryVariantsBatchSource(loader)
        filters.extend([
            DeleteAttributesFromVariantsBatchFilter(attributes_to_delete),
            AnnotationPipelineVariantsBatchFilter(pipeline),
            Schema2SummaryVariantBatchConsumer(writer),
        ])

    with PipelineProcessor(source, filters) as processor:
        processor.process_region(region)


def _build_argument_parser() -> argparse.ArgumentParser:
    """Construct and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Annotate Schema2 Parquet",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "input", default="-", nargs="?",
        help="the directory containing Parquet files")
    parser.add_argument(
        "-r", "--region",
        type=str, help="annotate only a specific region",
        default=None)
    parser.add_argument(
        "-s", "--region-size", default=300_000_000,
        type=int, help="region size to parallelize by")
    parser.add_argument(
        "-w", "--work-dir",
        help="Directory to store intermediate output files in",
        default="annotate_schema2_output")
    parser.add_argument(
        "-i", "--full-reannotation",
        help="Ignore any previous annotation and run "
        " a full reannotation.",
        action="store_true")
    output_behaviour = parser.add_mutually_exclusive_group()
    output_behaviour.add_argument(
        "-o", "--output",
        help="Path of the directory to hold the output")
    output_behaviour.add_argument(
        "-e", "--in-place",
        help="Produce output directly in given input dir.",
        action="store_true")
    output_behaviour.add_argument(
        "-m", "--meta",
        help="Print the input Parquet's meta properties.",
        action="store_true")
    output_behaviour.add_argument(
        "-n", "--dry-run",
        help="Print the annotation that will be done without writing.",
        action="store_true")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=0,  # 0 = annotate iteratively, no batches
        help="Annotate in batches of",
    )

    CLIAnnotationContextProvider.add_argparser_arguments(parser)
    TaskGraphCli.add_arguments(parser)
    VerbosityConfiguration.set_arguments(parser)
    return parser


def _print_meta(loader: ParquetLoader) -> None:
    """Print the metadata of a Parquet study."""
    for k, v in loader.meta.items():
        print("=" * 50)
        print(k)
        print("=" * 50)
        print(v)
        print()


def _remove_data(path: str) -> None:
    data_layout = create_schema2_dataset_layout(path)
    assert data_layout.family is not None
    assert data_layout.summary is not None

    pedigree = pathlib.Path(data_layout.pedigree).parent
    meta = pathlib.Path(data_layout.meta).parent
    family = pathlib.Path(data_layout.family)
    summary = pathlib.Path(data_layout.summary)

    shutil.rmtree(summary)
    shutil.rmtree(meta)

    if pedigree.is_symlink():
        pedigree.unlink()
    else:
        shutil.rmtree(pedigree)

    if family.is_symlink():
        family.unlink()
    else:
        shutil.rmtree(family)


def _setup_io_layouts(
    input_path: str,
    output_path: str,
    *,
    in_place: bool = False,
    force: bool = False,
) -> tuple[Schema2DatasetLayout, Schema2DatasetLayout]:
    """
    Produces the input and output dataset layouts for the tool to run.

    Additionally, carries out any transformations necessary to produce
    the layouts correctly, such as renaming, removing, etc.
    """
    if not in_place and not output_path:
        raise ValueError("No output path was provided!")

    input_dir = os.path.abspath(input_path)
    output_dir = input_dir if in_place\
        else os.path.abspath(output_path)

    if not in_place:
        if os.path.exists(output_dir) and not force:
            logger.warning(
                "Output path '%s' already exists! "
                "Some files may be overwritten.", output_dir,
            )
        elif os.path.exists(output_dir) and force:
            _remove_data(output_dir)

    input_layout = backup_schema2_study(input_dir) if in_place \
        else create_schema2_dataset_layout(input_dir)
    output_layout = create_schema2_dataset_layout(output_dir)

    if input_layout.summary is None:
        raise ValueError("Invalid summary dir in input layout!")
    if output_layout.summary is None:
        raise ValueError("Invalid summary dir in output layout!")
    if output_layout.family is None:
        raise ValueError("Invalid family dir in output layout!")

    return input_layout, output_layout


def _add_tasks_to_graph(  # pylint:disable=too-many-positional-arguments
    task_graph: TaskGraph,
    loader: ParquetLoader,
    output_layout: Schema2DatasetLayout,
    pipeline: ReannotationPipeline,
    grr: GenomicResourceRepo,
    region: str | None,
    args: _ProcessingArgs,
) -> None:
    annotation_tasks = produce_schema2_annotation_tasks(
        task_graph,
        loader,
        output_layout.study,
        pipeline.raw,
        grr,
        region,
        args,
    )

    annotation_sync = task_graph.create_task(
        "sync_parquet_write", lambda: None,
        args=[], deps=annotation_tasks,
    )

    produce_schema2_merging_tasks(
        task_graph,
        annotation_sync,
        ReferenceGenome(grr.get_resource(loader.meta["reference_genome"])),
        loader,
        output_layout,
    )


def cli(raw_args: list[str] | None = None) -> None:
    """Entry method for running the Schema2 Parquet annotation tool."""
    if not raw_args:
        raw_args = sys.argv[1:]

    arg_parser = _build_argument_parser()
    args = vars(arg_parser.parse_args(raw_args))

    input_dir = os.path.abspath(args["input"])

    if args["meta"]:
        _print_meta(ParquetLoader.load_from_dir(input_dir))
        return

    pipeline, _, grr = get_stuff_from_context(args)
    assert grr.definition is not None

    if args["dry_run"]:
        pipeline.print()
        return

    if not os.path.exists(args["work_dir"]):
        os.mkdir(args["work_dir"])
    args["task_status_dir"] = os.path.join(args["work_dir"], ".task-status")
    args["task_log_dir"] = os.path.join(args["work_dir"], ".task-log")

    # Is this too eager? What if a reannotation pipeline is created
    # inside work() and the only caching that must be done is far smaller
    # than the entire new annotation config suggests?
    cache_pipeline_resources(grr, pipeline)

    input_layout, output_layout = _setup_io_layouts(
        args["input"],
        args["output"],
        in_place=args["in_place"],
        force=args["force"],
    )
    loader = ParquetLoader(input_layout)
    write_new_meta(loader, pipeline, output_layout)
    if not args["in_place"]:
        symlink_pedigree_and_family_variants(loader.layout, output_layout)

    processing_args = _ProcessingArgs(
        args["work_dir"],
        args["batch_size"],
        args["region_size"],
        args["allow_repeated_attributes"],
        args["full_reannotation"],
    )

    task_graph = TaskGraph()
    _add_tasks_to_graph(
        task_graph,
        loader,
        output_layout,
        pipeline,
        grr,
        args["region"],
        processing_args,
    )

    if len(task_graph.tasks) > 0:
        add_input_files_to_task_graph(args, task_graph)
        TaskGraphCli.process_graph(task_graph, **args)
