import os
import pathlib
from datetime import datetime

import yaml

from dae.annotation.annotate_utils import AnnotationTool
from dae.annotation.annotation_config import (
    RawAnnotatorsConfig,
    RawPipelineConfig,
)
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    ReannotationPipeline,
)
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.parquet.parquet_writer import (
    append_meta_to_parquet,
    merge_variants_parquets,
    serialize_summary_schema,
)
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.parquet.schema2.parquet_io import VariantsParquetWriter
from dae.schema2_storage.schema2_layout import Schema2DatasetLayout
from dae.task_graph.graph import Task, TaskGraph
from dae.utils.regions import Region, split_into_regions
from dae.variants_loaders.parquet.loader import ParquetLoader


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


def annotate_parquet(
    input_layout: Schema2DatasetLayout,
    output_dir: str,
    pipeline_config: RawAnnotatorsConfig,
    region: str,
    grr_definition: dict,
    bucket_idx: int,
    allow_repeated_attributes: bool,  # noqa: FBT001
    full_reannotation: bool,  # noqa: FBT001
) -> None:
    """Run annotation over a given directory of Parquet files."""
    loader = ParquetLoader(input_layout)
    pipeline = AnnotationTool.produce_annotation_pipeline(
        pipeline_config,
        loader.meta["annotation_pipeline"] if loader.has_annotation else None,
        grr_definition,
        allow_repeated_attributes=allow_repeated_attributes,
        full_reannotation=full_reannotation,
    )

    writer = VariantsParquetWriter(
        output_dir, pipeline,
        loader.partition_descriptor,
        bucket_index=bucket_idx,
    )

    if isinstance(pipeline, ReannotationPipeline):
        internal_attributes = [
            attribute.name
            for annotator in (pipeline.annotators_new
                                | pipeline.annotators_rerun)
            for attribute in annotator.attributes
            if attribute.internal
        ]
    else:
        internal_attributes = [
            attribute.name
            for attribute in pipeline.get_attributes()
            if attribute.internal
        ]

    region_obj = Region.from_str(region)
    for variant in loader.fetch_summary_variants(region=region_obj):
        for allele in variant.alt_alleles:
            if isinstance(pipeline, ReannotationPipeline):
                result = pipeline.annotate_summary_allele(allele)
                for attr in pipeline.attributes_deleted:
                    del allele.attributes[attr]
            else:
                result = pipeline.annotate(allele.get_annotatable())
            for attr in internal_attributes:
                del result[attr]
            allele.update_attributes(result)
        writer.write_summary_variant(variant)

    writer.close()


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
    allow_repeated_attributes: bool,  # noqa: FBT001
    target_region: str | None = None,
    *,
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
            annotate_parquet,
            [loader.layout, output_dir,
             raw_pipeline, region, grr.definition,
             idx, allow_repeated_attributes, full_reannotation],
            [],
        ))
    return tasks


def produce_schema2_merging_tasks(
    task_graph: TaskGraph,
    annotation_tasks: list[Task],
    loader: ParquetLoader,
    output_layout: Schema2DatasetLayout,
) -> list[Task]:
    """Produce TaskGraph tasks for Parquet file merging."""

    if loader.layout.summary is None:
        raise ValueError("No summary variants to merge!")

    if loader.partitioned:
        to_join = [
            os.path.relpath(dirpath, loader.layout.summary)
            for dirpath, subdirs, _ in os.walk(loader.layout.summary)
            if not subdirs
        ]
        tasks = [
            task_graph.create_task(
                f"merge_{path}",
                merge_partitioned,
                [output_layout.summary,
                 path,
                 loader.partition_descriptor],
                annotation_tasks,
            ) for path in to_join
        ]
    else:
        tasks = [
            task_graph.create_task(
                "merge",
                merge_non_partitioned,
                [output_layout.summary],
                annotation_tasks,
            ),
        ]
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


def merge_partitioned(
    summary_dir: str,
    partition_dir: str,
    partition_descriptor: PartitionDescriptor,
) -> None:
    """Helper method to merge Parquet files in partitioned studies."""
    partitions = []
    for partition in partition_dir.split("/"):
        key, value = partition.split("=", maxsplit=1)
        partitions.append((key, value))
    output_dir = os.path.join(summary_dir, partition_dir)
    merge_variants_parquets(partition_descriptor, output_dir, partitions)


def merge_non_partitioned(output_dir: str) -> None:
    merge_variants_parquets(PartitionDescriptor(), output_dir, [])
