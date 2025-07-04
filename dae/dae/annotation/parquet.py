from __future__ import annotations

import logging
import os
import pathlib
from collections.abc import Iterable
from datetime import datetime
from typing import Any

import yaml

from dae.annotation.annotation_config import (
    RawPipelineConfig,
)
from dae.annotation.annotation_factory import build_annotation_pipeline
from dae.annotation.annotation_pipeline import (
    AnnotationPipeline,
    ReannotationPipeline,
)
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.repository import GenomicResourceRepo
from dae.genomic_resources.repository_factory import (
    build_genomic_resource_repository,
)
from dae.parquet.parquet_writer import (
    append_meta_to_parquet,
    merge_variants_parquets,
    serialize_summary_schema,
)
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.parquet.schema2.loader import ParquetLoader
from dae.parquet.schema2.processing_pipeline import (
    AnnotationPipelineVariantsFilter,
    DeleteAttributesFromVariantFilter,
    VariantsFilter,
    VariantsPipelineProcessor,
    VariantsSource,
)
from dae.parquet.schema2.variants_parquet_writer import VariantsParquetWriter
from dae.schema2_storage.schema2_layout import Schema2DatasetLayout
from dae.task_graph.graph import Task, TaskGraph
from dae.utils.regions import Region, split_into_regions
from dae.variants_loaders.raw.loader import FullVariant

logger = logging.getLogger("format_handlers")


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
                  output_dir, idx, work_dir, Region.from_str(region),
                  allow_repeated_attributes, full_reannotation],
            deps=[],
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
                args=[
                    output_layout.summary,
                    path,
                    loader.partition_descriptor],
                deps=annotation_tasks,
            ) for path in to_join
        ]
    else:
        tasks = [
            task_graph.create_task(
                "merge",
                merge_non_partitioned,
                args=[output_layout.summary],
                deps=annotation_tasks,
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


class ParquetVariantsSource(VariantsSource):
    """Producer for variants from a Parquet dataset."""
    def __init__(self, input_layout: Schema2DatasetLayout):
        self.input_layout = input_layout
        self.input_loader = ParquetLoader(self.input_layout)

    def __enter__(self) -> ParquetVariantsSource:
        return self

    def __exit__(
        self, exc_type: Any | None, exc_value: Any | None, exc_tb: Any | None,
    ) -> None:
        pass

    def fetch(
        self, region: Region | None = None,
    ) -> Iterable[FullVariant]:
        assert self.input_loader is not None
        for sv in self.input_loader.fetch_summary_variants(region=region):
            yield FullVariant(sv, ())


class ParquetSummaryVariantConsumer(VariantsParquetWriter):
    """Consumer for Parquet summary variants."""
    def consume_one(self, full_variant: FullVariant) -> None:
        summary_index = self.summary_index
        sj_base_index = self._calc_sj_base_index(summary_index)
        self.write_summary_variant(
            full_variant.summary_variant,
            sj_base_index=sj_base_index,
        )
        self.summary_index += 1


def process_parquet(
    input_layout: Schema2DatasetLayout,
    pipeline_config: RawPipelineConfig,
    grr_definition: dict | None,
    output_dir: str,
    bucket_idx: int,
    work_dir: str,
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

    source = ParquetVariantsSource(loader.layout)
    filters: list[VariantsFilter] = [
        AnnotationPipelineVariantsFilter(pipeline),
    ]
    if isinstance(pipeline, ReannotationPipeline):
        # FIXME This prevents using deleted attributes in the pipeline
        # as it will delete them before the pipeline is ran
        filters.insert(
            0,
            DeleteAttributesFromVariantFilter(pipeline.attributes_deleted),
            )
    consumer = ParquetSummaryVariantConsumer(
        output_dir,
        pipeline.get_attributes(),
        loader.partition_descriptor,
        bucket_index=bucket_idx,
        variants_blob_serializer=variants_blob_serializer,
    )

    with VariantsPipelineProcessor(source, filters, consumer) as processor:
        processor.process_region(region)
