import logging
import os
from collections.abc import Generator

import yaml
from pyarrow import parquet as pq

from dae.import_tools.import_tools import Bucket, ImportProject, ImportStorage
from dae.parquet.parquet_writer import (
    append_meta_to_parquet,
    collect_pedigree_parquet_schema,
    fill_family_bins,
    merge_variants_parquets,
    save_ped_df_to_parquet,
    serialize_summary_schema,
    serialize_variants_data_schema,
)
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.parquet.schema2.parquet_io import (
    VariantsParquetWriter,
)
from dae.parquet.schema2.serializers import AlleleParquetSerializer
from dae.parquet.schema2.variant_serializers import (
    ZstdIndexedVariantsDataSerializer,
)
from dae.schema2_storage.schema2_layout import (
    Schema2DatasetLayout,
    create_schema2_dataset_layout,
)
from dae.task_graph.graph import Task, TaskGraph
from dae.utils import fs_utils

logger = logging.getLogger(__name__)


def schema2_project_dataset_layout(
        project: ImportProject) -> Schema2DatasetLayout:
    study_dir = fs_utils.join(project.work_dir, project.study_id)
    return create_schema2_dataset_layout(study_dir)


class Schema2ImportStorage(ImportStorage):
    """Import logic for data in the Impala Schema 1 format."""

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
    def _serialize_variants_data_schema(cls, project: ImportProject) -> str:
        annotation_pipeline = project.build_annotation_pipeline()
        return serialize_variants_data_schema(
            annotation_pipeline.get_attributes(),
        )

    @classmethod
    def _serialize_summary_schema(cls, project: ImportProject) -> str:
        annotation_pipeline = project.build_annotation_pipeline()
        return serialize_summary_schema(
            annotation_pipeline.get_attributes(),
            project.get_partition_descriptor(),
        )

    @classmethod
    def _serialize_family_schema(cls, project: ImportProject) -> str:
        summary_schema = AlleleParquetSerializer.build_family_schema()
        schema = [
            (f.name, f.type) for f in summary_schema
        ]
        partition_descriptor = cls._get_partition_description(project)
        schema.extend(
            list(partition_descriptor.dataset_family_partition()))
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
        annotation_pipeline = yaml.dump(annotation_pipeline_config)
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

                "variants_data_schema",
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

                cls._serialize_variants_data_schema(project),
            ])

    @classmethod
    def _do_write_variant(
            cls, project: ImportProject, bucket: Bucket) -> None:
        layout = schema2_project_dataset_layout(project)
        gpf_instance = project.get_gpf_instance()
        variants_loader = project.get_variant_loader(
            bucket, reference_genome=gpf_instance.reference_genome)
        variants_loader = project.build_variants_loader_pipeline(
            variants_loader,
        )
        if bucket.region_bin is not None and bucket.region_bin != "none":
            logger.info(
                "resetting regions (rb: %s): %s",
                bucket.region_bin, bucket.regions)
            variants_loader.reset_regions(bucket.regions)

        row_group_size = project.get_row_group_size()
        logger.debug("argv.rows: %s", row_group_size)
        annotation_pipeline = project.build_annotation_pipeline()

        meta = ZstdIndexedVariantsDataSerializer.build_serialization_meta(
            [
                attr.name
                for attr in annotation_pipeline.get_attributes()
                if not attr.internal
            ])
        serializer = ZstdIndexedVariantsDataSerializer(meta)

        variants_writer = VariantsParquetWriter(
            out_dir=layout.study,
            annotation_schema=annotation_pipeline.get_attributes(),
            partition_descriptor=cls._get_partition_description(project),
            serializer=serializer,
            bucket_index=bucket.index,
            row_group_size=row_group_size,
            include_reference=project.include_reference,
        )
        variants_writer.write_dataset(
            variants_loader.full_variants_iterator(),
        )

    @classmethod
    def _variant_partitions(
        cls, project: ImportProject,
    ) -> Generator[tuple[str, list[tuple[str, str]]], None, None]:
        part_desc = cls._get_partition_description(project)
        chromosomes = project.get_variant_loader_chromosomes()
        chromosome_lengths = dict(filter(
            lambda cl: cl[0] in chromosomes,
            project.get_gpf_instance()
            .reference_genome
            .get_all_chrom_lengths()))
        sum_parts, fam_parts = \
            part_desc.get_variant_partitions(chromosome_lengths)
        if len(sum_parts) == 0:
            yield part_desc.partition_directory("summary", []), \
                [("summary", "single_bucket")]
        else:
            for part in sum_parts:
                yield part_desc.partition_directory("summary", part), part
        if len(fam_parts) == 0:
            yield part_desc.partition_directory("family", []), \
                [("family", "single_bucket")]
        else:
            for part in fam_parts:
                yield part_desc.partition_directory("family", part), part

    @classmethod
    def _merge_parquets(
        cls,
        project: ImportProject, out_dir: str, partitions: list[tuple[str, str]],
    ) -> None:
        layout = schema2_project_dataset_layout(project)
        full_out_dir = fs_utils.join(layout.study, out_dir)

        row_group_size = project.get_row_group_size()
        logger.debug("argv.rows: %s", row_group_size)

        merge_variants_parquets(
            cls._get_partition_description(project), full_out_dir, partitions,
            row_group_size=row_group_size,
        )

    def _build_all_parquet_tasks(
            self, project: ImportProject, graph: TaskGraph) -> list[Task]:
        pedigree_task = graph.create_task(
            "write_pedigree", self._do_write_pedigree, [project], [],
            input_files=[project.get_pedigree_filename()],
        )
        meta_task = graph.create_task(
            "write_meta", self._do_write_meta, [project], [])

        bucket_tasks = []
        for bucket in project.get_import_variants_buckets():
            task = graph.create_task(
                f"write_variants_{bucket}", self._do_write_variant,
                [project, bucket], [],
                input_files=project.get_input_filenames(bucket),
            )
            bucket_tasks.append(task)

        # merge small parquet files into larger ones
        bucket_sync = graph.create_task(
            "sync_parquet_write", lambda: None, [], bucket_tasks,
        )
        output_dir_tasks = []
        for output_dir, partitions in self._variant_partitions(project):
            output_dir_tasks.append(graph.create_task(
                f"merge_parquet_files_{output_dir}", self._merge_parquets,
                [project, output_dir, partitions], [bucket_sync],
            ))

        # dummy task used for running the parquet generation
        all_parquet_task = graph.create_task(
            "all_parquet_tasks", lambda: None, [],
            [*output_dir_tasks, bucket_sync],
        )
        return [pedigree_task, meta_task, all_parquet_task]

    def generate_import_task_graph(
            self, project: ImportProject) -> TaskGraph:
        graph = TaskGraph()
        if project.get_processing_parquet_dataset_dir() is None:
            self._build_all_parquet_tasks(project, graph)

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
