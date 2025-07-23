from __future__ import annotations

import argparse
import itertools
import logging
import operator
import os
import pathlib
import shutil
from datetime import datetime

import yaml

from dae.annotation.annotate_utils import AnnotationTool
from dae.annotation.annotation_config import (
    RawPipelineConfig,
)
from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    ReannotationPipeline,
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


def produce_schema2_annotation_tasks(
    task_graph: TaskGraph,
    loader: ParquetLoader,
    output_dir: str,
    raw_pipeline: RawPipelineConfig,
    grr: GenomicResourceRepo,
    region_size: int,
    work_dir: str,
    batch_size: int,
    *,
    target_region: str | None = None,
    allow_repeated_attributes: bool = False,
    full_reannotation: bool = False,
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

    regions = produce_regions(target_region, region_size, contig_lens)
    tasks = []
    for idx, region in enumerate(regions):
        tasks.append(task_graph.create_task(
            f"part_{region}",
            process_parquet,
            args=[loader.layout, raw_pipeline, grr.definition,
                  output_dir, idx, work_dir,
                  batch_size, Region.from_str(region),
                  allow_repeated_attributes, full_reannotation],
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
    pipeline: AnnotationPipeline,
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


def process_parquet(
    input_layout: Schema2DatasetLayout,
    pipeline_config: RawPipelineConfig,
    grr_definition: dict | None,
    output_dir: str,
    bucket_idx: int,
    work_dir: str,
    batch_size: int,
    region: Region,
    allow_repeated_attributes: bool,  # noqa: FBT001
    full_reannotation: bool,  # noqa: FBT001
) -> None:
    """Process a Parquet dataset for annotation."""
    loader = ParquetLoader(input_layout)
    grr = build_genomic_resource_repository(definition=grr_definition)
    pipeline_config_old = loader.meta["annotation_pipeline"] \
        if loader.has_annotation else None
    variants_blob_serializer = loader.meta.get(
        "variants_blob_serializer",
        "json",
    )

    pipeline = build_annotation_pipeline(
        pipeline_config, grr,
        allow_repeated_attributes=allow_repeated_attributes,
        work_dir=pathlib.Path(work_dir),
        config_old_raw=pipeline_config_old,
        full_reannotation=full_reannotation,
    )

    writer = VariantsParquetWriter(
        output_dir,
        pipeline.get_attributes(),
        loader.partition_descriptor,
        bucket_index=bucket_idx,
        variants_blob_serializer=variants_blob_serializer,
    )

    source: Source
    filters: list[Filter] = []

    if batch_size <= 0:
        source = Schema2SummaryVariantsSource(loader)
        if isinstance(pipeline, ReannotationPipeline):
            filters.append(DeleteAttributesFromVariantFilter(
                pipeline.attributes_deleted))
        filters.extend([
            AnnotationPipelineVariantsFilter(pipeline),
            Schema2SummaryVariantConsumer(writer),
        ])
    else:
        source = Schema2SummaryVariantsBatchSource(loader)
        if isinstance(pipeline, ReannotationPipeline):
            filters.append(DeleteAttributesFromVariantsBatchFilter(
                pipeline.attributes_deleted))
        filters.extend([
            AnnotationPipelineVariantsBatchFilter(pipeline),
            Schema2SummaryVariantBatchConsumer(writer),
        ])

    with PipelineProcessor(source, filters) as processor:
        processor.process_region(region)


class AnnotateSchema2ParquetTool(AnnotationTool):
    """Annotation tool for the Parquet file format."""

    def __init__(self, raw_args: list[str] | None = None):
        super().__init__(raw_args)

        self.loader: ParquetLoader | None = None
        self.output_layout: Schema2DatasetLayout | None = None

    def get_argument_parser(self) -> argparse.ArgumentParser:
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

    def print_meta(self) -> None:
        """Print the metadata of a Parquet study."""
        input_dir = os.path.abspath(self.args["input"])
        if self.args["meta"]:
            loader = ParquetLoader.load_from_dir(input_dir)
            for k, v in loader.meta.items():
                print("=" * 50)
                print(k)
                print("=" * 50)
                print(v)
                print()

    def dry_run(self) -> None:
        """Print a summary of the annotation without running it."""
        assert self.pipeline is not None
        self.pipeline.print()

    def _remove_data(self, path: str) -> None:
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

    def _setup_io_layouts(self) -> tuple[Schema2DatasetLayout,
                                         Schema2DatasetLayout]:
        """
        Produces the input and output dataset layouts for the tool to run.

        Additionally, carries out any transformations necessary to produce
        the layouts correctly, such as renaming, removing, etc.
        """
        if not self.args["in_place"] and not self.args["output"]:
            raise ValueError("No output path was provided!")

        input_dir = os.path.abspath(self.args["input"])
        output_dir = input_dir if self.args["in_place"]\
            else os.path.abspath(self.args["output"])

        if not self.args["in_place"]:
            if os.path.exists(output_dir) and not self.args["force"]:
                logger.warning(
                    "Output path '%s' already exists! "
                    "Some files may be overwritten.", output_dir,
                )
            elif os.path.exists(output_dir) and self.args["force"]:
                self._remove_data(output_dir)

        input_layout = backup_schema2_study(input_dir) if self.args["in_place"]\
            else create_schema2_dataset_layout(input_dir)
        output_layout = create_schema2_dataset_layout(output_dir)

        if input_layout.summary is None:
            raise ValueError("Invalid summary dir in input layout!")
        if output_layout.summary is None:
            raise ValueError("Invalid summary dir in output layout!")
        if output_layout.family is None:
            raise ValueError("Invalid family dir in output layout!")

        return input_layout, output_layout

    def prepare_for_annotation(self) -> None:
        assert self.pipeline is not None

        input_layout, self.output_layout = self._setup_io_layouts()
        self.loader = ParquetLoader(input_layout)
        write_new_meta(self.loader, self.pipeline, self.output_layout)
        if not self.args["in_place"]:
            symlink_pedigree_and_family_variants(self.loader.layout,
                                                 self.output_layout)

    def add_tasks_to_graph(self, task_graph: TaskGraph) -> None:
        assert self.loader is not None
        assert self.output_layout is not None
        assert self.pipeline is not None

        annotation_tasks = produce_schema2_annotation_tasks(
            task_graph,
            self.loader,
            self.output_layout.study,
            self.pipeline.raw,
            self.grr,
            self.args["region_size"],
            self.args["work_dir"],
            self.args["batch_size"],
            target_region=self.args["region"],
            allow_repeated_attributes=self.args["allow_repeated_attributes"],
            full_reannotation=self.args["full_reannotation"],
        )

        annotation_sync = task_graph.create_task(
            "sync_parquet_write", lambda: None,
            args=[], deps=annotation_tasks,
        )

        produce_schema2_merging_tasks(
            task_graph,
            annotation_sync,
            ReferenceGenome(
                self.grr.get_resource(self.loader.meta["reference_genome"])),
            self.loader,
            self.output_layout,
        )


def cli(
    raw_args: list[str] | None = None,
) -> None:
    """Entry method for AnnotateSchema2ParquetTool."""
    tool = AnnotateSchema2ParquetTool(raw_args)
    if tool.args["meta"]:
        tool.print_meta()
        return
    if tool.args["dry_run"]:
        tool.dry_run()
        return
    tool.run()
