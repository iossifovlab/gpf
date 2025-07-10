import itertools
import logging
import operator
import os
import pathlib
from typing import Literal

import yaml
from pyarrow import parquet as pq

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.import_tools.import_tools import (
    Bucket,
    ImportProject,
    ImportStorage,
    construct_import_annotation_pipeline,
)
from dae.parquet.parquet_writer import (
    append_meta_to_parquet,
    collect_pedigree_parquet_schema,
    fill_family_bins,
    save_ped_df_to_parquet,
    serialize_summary_schema,
)
from dae.parquet.partition_descriptor import (
    Partition,
    PartitionDescriptor,
)
from dae.parquet.schema2.annotate_schema2_parquet import (
    backup_schema2_study,
    produce_schema2_annotation_tasks,
    produce_schema2_merging_tasks,
    write_new_meta,
)
from dae.parquet.schema2.loader import ParquetLoader
from dae.parquet.schema2.merge_parquet import merge_parquet_directory
from dae.parquet.schema2.processing_pipeline import (
    AnnotationPipelineVariantsBatchFilter,
    AnnotationPipelineVariantsFilter,
    VariantsLoaderBatchSource,
    VariantsLoaderSource,
    VariantsPipelineProcessor,
)
from dae.parquet.schema2.serializers import (
    VariantsDataSerializer,
    build_family_schema,
    build_summary_blob_schema,
)
from dae.parquet.schema2.variants_parquet_writer import (
    Schema2VariantBatchConsumer,
    Schema2VariantConsumer,
    VariantsParquetWriter,
)
from dae.schema2_storage.schema2_layout import (
    Schema2DatasetLayout,
    create_schema2_dataset_layout,
)
from dae.task_graph.graph import Task, TaskGraph
from dae.utils import fs_utils
from dae.utils.processing_pipeline import Filter, Source
from dae.utils.regions import Region

logger = logging.getLogger(__name__)


def schema2_project_dataset_layout(
    project: ImportProject,
) -> Schema2DatasetLayout:
    study_dir = fs_utils.join(project.work_dir, project.study_id)
    return create_schema2_dataset_layout(study_dir)


class Schema2ImportStorage(ImportStorage):
    """Import logic for data in the Schema 2 format."""

    BATCH_SIZE = 1_000

    @staticmethod
    def _get_partition_description(
            project: ImportProject,
            out_dir: str | None = None) -> PartitionDescriptor:
        out_dir = out_dir or project.work_dir
        return project.get_partition_descriptor()

    @classmethod
    def _do_write_pedigree(cls, project: ImportProject) -> None:
        layout = schema2_project_dataset_layout(project)
        families = project.get_pedigree()
        partition_descriptor = cls._get_partition_description(project)
        fill_family_bins(families, partition_descriptor)
        dirname = os.path.dirname(layout.pedigree)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        save_ped_df_to_parquet(
            families.ped_df, layout.pedigree)

    @classmethod
    def _serialize_summary_schema(cls, project: ImportProject) -> str:
        annotation_pipeline = project.build_annotation_pipeline()
        return serialize_summary_schema(
            annotation_pipeline.get_attributes(),
            project.get_partition_descriptor(),
        )

    @classmethod
    def _serialize_family_schema(cls, project: ImportProject) -> str:
        summary_schema = build_family_schema()
        schema = [
            (f.name, f.type) for f in summary_schema
        ]
        partition_descriptor = cls._get_partition_description(project)
        schema.extend(
            list(partition_descriptor.family_partition_schema()))
        return "\n".join([
            f"{n}|{t}" for n, t in schema
        ])

    @classmethod
    def _serialize_pedigree_schema(cls, project: ImportProject) -> str:
        families = project.get_pedigree()
        partition_descriptor = cls._get_partition_description(project)
        fill_family_bins(families, partition_descriptor)

        pedigree_schema = collect_pedigree_parquet_schema(
            families.ped_df)
        return "\n".join([
            f"{f.name}|{f.type}" for f in pedigree_schema])

    @classmethod
    def _do_write_meta(cls, project: ImportProject) -> None:
        layout = schema2_project_dataset_layout(project)
        gpf_instance = project.get_gpf_instance()

        reference_genome = gpf_instance.reference_genome.resource_id
        gene_models = gpf_instance.gene_models.resource_id
        annotation_pipeline_config = project.get_annotation_pipeline_config()
        annotation_pipeline = yaml.safe_dump(annotation_pipeline_config)
        variants_types = project.get_variant_loader_types()
        contigs = ",".join(
            [f"{k}={v}" for k, v
             in project.get_variant_loader_chrom_lens().items()],
        )
        study_config = {
            "conf_dir": ".",
            "has_denovo": project.has_denovo_variants(),
            "has_cnv": "cnv" in variants_types,
            "has_transmitted": bool({"dae", "vcf"} & variants_types),
            "genotype_browser": {"enabled": True},
        }
        study = yaml.dump(study_config)

        append_meta_to_parquet(
            layout.meta,
            [
                "partition_description",
                "summary_schema",
                "family_schema",
                "pedigree_schema",

                "reference_genome",
                "gene_models",
                "annotation_pipeline",
                "study",
                "contigs",
                "variants_blob_serializer",
            ],
            [
                cls._get_partition_description(project).serialize(),
                cls._serialize_summary_schema(project),
                cls._serialize_family_schema(project),
                cls._serialize_pedigree_schema(project),

                reference_genome,
                gene_models,
                annotation_pipeline,
                study,
                contigs,
                project.get_variants_blob_serializer(),
            ])

    @classmethod
    def _create_import_processing_pipeline(
        cls, project: ImportProject,
        bucket: Bucket,
        row_group_size: int | None = None,
    ) -> VariantsPipelineProcessor:
        """Create the import processing pipeline."""
        layout = schema2_project_dataset_layout(project)
        gpf_instance = project.get_gpf_instance()

        variants_loader = project.get_variant_loader(
            bucket, reference_genome=gpf_instance.reference_genome)
        if row_group_size is None:
            row_group_size = cls.BATCH_SIZE

        logger.debug("argv.rows: %s", row_group_size)
        annotation_pipeline = project.build_annotation_pipeline()

        blob_serializer = VariantsDataSerializer.build_serializer(
            build_summary_blob_schema(
                annotation_pipeline.get_attributes(),
            ),
            project.get_variants_blob_serializer(),
        )

        batch_size = project.get_processing_annotation_batch_size()

        writer = VariantsParquetWriter(
            out_dir=layout.study,
            annotation_schema=annotation_pipeline.get_attributes(),
            partition_descriptor=cls._get_partition_description(project),
            blob_serializer=blob_serializer,
            bucket_index=bucket.index,
            row_group_size=row_group_size,
            include_reference=project.include_reference,
        )

        source: Source
        filters: list[Filter] = []
        if batch_size == 0:
            source = VariantsLoaderSource(variants_loader)
            filters.extend([
                AnnotationPipelineVariantsFilter(annotation_pipeline),
                Schema2VariantConsumer(writer),
            ])
        else:
            source = VariantsLoaderBatchSource(
                variants_loader, batch_size=batch_size)
            filters.extend([
                AnnotationPipelineVariantsBatchFilter(annotation_pipeline),
                Schema2VariantBatchConsumer(writer),
            ])

        return VariantsPipelineProcessor(source, filters)

    @classmethod
    def _do_write_variant(
            cls, project: ImportProject, bucket: Bucket) -> None:
        regions: list[Region] | None = None
        if bucket.region_bin is not None and \
                bucket.region_bin not in {"none", "all"}:
            logger.info(
                "creating regions (rb: %s): %s",
                bucket.region_bin, bucket.regions)
            regions = [
                Region.from_str(r) for r in bucket.regions]

        processing_pipeline = cls._create_import_processing_pipeline(
            project, bucket,
        )
        with processing_pipeline as pipeline:
            pipeline.process(regions)

    @classmethod
    def _merge_parquets(
        cls,
        project: ImportProject,
        variants_type: Literal["summary", "family"],
        partitions: list[Partition],
    ) -> None:
        partition_descriptor = cls._get_partition_description(project)
        row_group_size = project.get_row_group_size()
        logger.debug("argv.rows: %s", row_group_size)

        layout = schema2_project_dataset_layout(project)

        for partition in partitions:
            out_dir = partition_descriptor.partition_directory(
                    variants_type, partition)

            variants_dir = fs_utils.join(layout.study, out_dir)

            output_parquet_file = fs_utils.join(
                variants_dir,
                partition_descriptor.partition_filename(
                    "merged", partition, bucket_index=None,
                ),
            )

            merge_parquet_directory(
                variants_dir, output_parquet_file,
                row_group_size=row_group_size,
                variants_type=variants_type,
            )

    def _build_all_parquet_tasks(
            self, project: ImportProject, graph: TaskGraph) -> list[Task]:
        pedigree_task = graph.create_task(
            "write_pedigree", self._do_write_pedigree,
            args=[project], deps=[],
            input_files=[project.get_pedigree_filename()],
        )
        meta_task = graph.create_task(
            "write_meta", self._do_write_meta,
            args=[project], deps=[])

        bucket_tasks = []
        for bucket in project.get_import_variants_buckets():
            task = graph.create_task(
                f"write_variants_{bucket}", self._do_write_variant,
                args=[project, bucket], deps=[],
                input_files=project.get_input_filenames(bucket),
            )
            bucket_tasks.append(task)

        # merge small parquet files into larger ones
        bucket_sync = graph.create_task(
            "sync_parquet_write", lambda: None,
            args=[], deps=bucket_tasks,
        )

        reference_genome = project.get_gpf_instance().reference_genome
        chromosome_lengths = reference_genome.get_all_chrom_lengths()
        part_desc = project.get_partition_descriptor()
        summary_merge_tasks = []
        for region_bin, group in itertools.groupby(
                part_desc.build_summary_partitions(chromosome_lengths),
                operator.attrgetter("region_bin")):
            partitions = list(group)
            if len(partitions) == 0:
                continue
            task = graph.create_task(
                f"merge_parquet_files_summary_region_bin_{region_bin}",
                self._merge_parquets,
                args=[project, "summary", partitions],
                deps=[bucket_sync],
            )
            summary_merge_tasks.append(task)

        family_merge_tasks = []
        for region_bin, group in itertools.groupby(
                part_desc.build_family_partitions(chromosome_lengths),
                operator.attrgetter("region_bin")):
            partitions = list(group)
            if len(partitions) == 0:
                continue

            task = graph.create_task(
                f"merge_parquet_files_family_{region_bin}",
                self._merge_parquets,
                args=[project, "family", partitions],
                deps=[bucket_sync],
            )
            family_merge_tasks.append(task)

        all_parquet_task = graph.create_task(
            "all_parquet_tasks", lambda: None,
            args=[],
            deps=[*summary_merge_tasks, *family_merge_tasks, bucket_sync],
        )
        return [pedigree_task, meta_task, all_parquet_task]

    def generate_import_task_graph(
            self, project: ImportProject) -> TaskGraph:
        graph = TaskGraph()
        if project.get_processing_parquet_dataset_dir() is None:
            self._build_all_parquet_tasks(project, graph)

        return graph

    @staticmethod
    def generate_reannotate_task_graph(
        gpf_instance: GPFInstance,
        study_dir: str,
        region_size: int,
        work_dir: pathlib.Path,
        *,
        allow_repeated_attributes: bool = False,
        full_reannotation: bool = False,
    ) -> TaskGraph:
        """Generate TaskGraph for reannotation of a given study."""
        graph = TaskGraph()

        pipeline = construct_import_annotation_pipeline(gpf_instance,
                                                        work_dir=work_dir)
        study_layout = create_schema2_dataset_layout(study_dir)
        backup_layout = backup_schema2_study(study_dir)
        loader = ParquetLoader(backup_layout)

        write_new_meta(loader, pipeline, study_layout)

        annotation_tasks = produce_schema2_annotation_tasks(
            graph,
            loader,
            study_dir,
            pipeline.raw,
            gpf_instance.grr,
            region_size,
            str(work_dir),
            0,
            allow_repeated_attributes=allow_repeated_attributes,
            full_reannotation=full_reannotation,
        )

        annotation_sync = graph.create_task(
            "sync_parquet_write", lambda: None,
            args=[], deps=annotation_tasks,
        )

        produce_schema2_merging_tasks(
            graph,
            annotation_sync,
            gpf_instance.reference_genome,
            loader,
            study_layout,
        )
        return graph

    @staticmethod
    def load_meta(project: ImportProject) -> dict[str, str]:
        """Load meta data from the parquet dataset."""
        parquet_dir = project.get_parquet_dataset_dir()
        if parquet_dir is None:
            raise ValueError("parquet dataset not stored: {project.study_id}")
        layout = create_schema2_dataset_layout(parquet_dir)

        table = pq.read_table(layout.meta)
        result = {}
        for rec in table.to_pandas().to_dict(orient="records"):
            result[rec["key"]] = rec["value"]
        return result
