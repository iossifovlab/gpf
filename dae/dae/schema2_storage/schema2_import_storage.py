import os
import logging
from dataclasses import dataclass
from typing import Optional, Generator

import yaml

from dae.utils import fs_utils
from dae.import_tools.import_tools import ImportStorage, ImportProject, \
    Bucket
from dae.task_graph.graph import TaskGraph, Task
from dae.parquet.parquet_writer import fill_family_bins, \
    save_ped_df_to_parquet, merge_parquets, append_meta_to_parquet
from dae.parquet.schema2.parquet_io import VariantsParquetWriter
from dae.parquet.partition_descriptor import PartitionDescriptor


logger = logging.getLogger(__file__)


@dataclass(frozen=True)
class Schema2DatasetLayout:
    study: str
    pedigree: str
    summary: Optional[str]
    family: Optional[str]
    meta: str
    base_dir: Optional[str] = None


def schema2_dataset_layout(study_dir: str) -> Schema2DatasetLayout:
    return Schema2DatasetLayout(
        study_dir,
        fs_utils.join(study_dir, "pedigree", "pedigree.parquet"),
        fs_utils.join(study_dir, "summary"),
        fs_utils.join(study_dir, "family"),
        fs_utils.join(study_dir, "meta", "meta.parquet"))


def schema2_project_dataset_layout(
        project: ImportProject) -> Schema2DatasetLayout:
    study_dir = fs_utils.join(project.work_dir, project.study_id)
    return schema2_dataset_layout(study_dir)


class Schema2ImportStorage(ImportStorage):
    """Import logic for data in the Impala Schema 1 format."""

    @staticmethod
    def _get_partition_description(
            project: ImportProject,
            out_dir: Optional[str] = None) -> PartitionDescriptor:
        out_dir = out_dir if out_dir else project.work_dir
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
    def _do_write_meta(cls, project: ImportProject) -> None:
        layout = schema2_project_dataset_layout(project)
        gpf_instance = project.get_gpf_instance()
        loader_type = next(iter(project.get_variant_loader_types()))
        gpf_instance = project.get_gpf_instance()
        variants_loader = project.get_variant_loader(
            loader_type=loader_type,
            reference_genome=gpf_instance.reference_genome)
        variants_loader = project.build_variants_loader_pipeline(
            variants_loader, gpf_instance
        )
        writer = VariantsParquetWriter(
            out_dir=layout.study,
            variants_loader=variants_loader,
            partition_descriptor=cls._get_partition_description(project)
        )
        writer.write_metadata()

        reference_genome = gpf_instance.reference_genome.resource_id
        gene_models = gpf_instance.gene_models.resource_id
        annotation_pipeline_config = project.get_annotation_pipeline_config(
            gpf_instance
        )
        annotation_pipeline = yaml.dump(annotation_pipeline_config)
        variants_types = project.get_variant_loader_types()
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
                "reference_genome",
                "gene_models",
                "annotation_pipeline",
                "study"
            ],
            [
                reference_genome,
                gene_models,
                annotation_pipeline,
                study
            ])

    @classmethod
    def _do_write_variant(
            cls, project: ImportProject, bucket: Bucket) -> None:
        layout = schema2_project_dataset_layout(project)
        gpf_instance = project.get_gpf_instance()
        variants_loader = project.get_variant_loader(
            bucket, reference_genome=gpf_instance.reference_genome)
        variants_loader = project.build_variants_loader_pipeline(
            variants_loader, gpf_instance
        )
        if bucket.region_bin is not None and bucket.region_bin != "none":
            logger.info(
                "resetting regions (rb: %s): %s",
                bucket.region_bin, bucket.regions)
            variants_loader.reset_regions(bucket.regions)

        rows = project.get_row_group_size(bucket)
        logger.debug("argv.rows: %s", rows)

        variants_writer = VariantsParquetWriter(
            out_dir=layout.study,
            variants_loader=variants_loader,
            partition_descriptor=cls._get_partition_description(project),
            bucket_index=bucket.index,
            rows=rows,
            include_reference=project.include_reference,
        )
        variants_writer.write_dataset()

    @classmethod
    def _variant_partitions(
        cls, project: ImportProject
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
        project: ImportProject, out_dir: str, partitions: list[tuple[str, str]]
    ) -> None:
        layout = schema2_project_dataset_layout(project)
        full_out_dir = fs_utils.join(layout.study, out_dir)
        merge_parquets(
            cls._get_partition_description(project), full_out_dir, partitions
        )

    def _build_all_parquet_tasks(
            self, project: ImportProject, graph: TaskGraph) -> list[Task]:
        pedigree_task = graph.create_task(
            "Generating Pedigree", self._do_write_pedigree, [project], [],
            input_files=[project.get_pedigree_filename()]
        )
        meta_task = graph.create_task(
            "Write Meta", self._do_write_meta, [project], [])

        bucket_tasks = []
        for bucket in project.get_import_variants_buckets():
            task = graph.create_task(
                f"Converting Variants {bucket}", self._do_write_variant,
                [project, bucket], [],
                input_files=project.get_input_filenames(bucket)
            )
            bucket_tasks.append(task)

        # merge small parquet files into larger ones
        bucket_sync = graph.create_task(
            "Sync Parquet Generation", lambda: None, [], bucket_tasks
        )
        output_dir_tasks = []
        for output_dir, partitions in self._variant_partitions(project):
            output_dir_tasks.append(graph.create_task(
                f"Merging {output_dir}", self._merge_parquets,
                [project, output_dir, partitions], [bucket_sync]
            ))

        # dummy task used for running the parquet generation w/o impala import
        all_parquet_task = graph.create_task(
            "Parquet Tasks", lambda: None, [], output_dir_tasks + [bucket_sync]
        )
        return [pedigree_task, meta_task, all_parquet_task]

    def generate_import_task_graph(
            self, project: ImportProject) -> TaskGraph:
        graph = TaskGraph()
        if project.get_processing_parquet_dataset_dir() is None:
            self._build_all_parquet_tasks(project, graph)

        return graph
