import logging
from dataclasses import dataclass
from typing import Optional

from dae.utils import fs_utils
from dae.import_tools.import_tools import ImportStorage
from dae.task_graph.graph import TaskGraph
from dae.parquet.parquet_writer import ParquetWriter
from dae.parquet.schema2.parquet_io import \
    VariantsParquetWriter as S2VariantsWriter
from dae.parquet.partition_descriptor import PartitionDescriptor


logger = logging.getLogger(__file__)


@dataclass(frozen=True)
class Schema2DatasetLayout:
    study: str
    pedigree: str
    summary: Optional[str]
    family: Optional[str]
    meta: Optional[str]


def schema2_dataset_layout(study_dir: str) -> Schema2DatasetLayout:
    return Schema2DatasetLayout(
        study_dir,
        fs_utils.join(study_dir, "pedigree", "pedigree.parquet"),
        fs_utils.join(study_dir, "summary"),
        fs_utils.join(study_dir, "family"),
        fs_utils.join(study_dir, "meta", "meta.parquet"))


def schema2_project_dataset_layout(project) -> Schema2DatasetLayout:
    study_dir = fs_utils.join(project.work_dir, project.study_id)
    return schema2_dataset_layout(study_dir)


class Schema2ImportStorage(ImportStorage):
    """Import logic for data in the Impala Schema 1 format."""

    @staticmethod
    def _get_partition_description(project, out_dir=None):
        out_dir = out_dir if out_dir else project.work_dir
        config_dict = project.get_partition_description_dict()

        if config_dict is None:
            return PartitionDescriptor()
        return PartitionDescriptor.parse_dict(config_dict)

    @classmethod
    def _do_write_pedigree(cls, project):
        layout = schema2_project_dataset_layout(project)
        ParquetWriter.write_pedigree(
            layout.pedigree, project.get_pedigree(),
            cls._get_partition_description(project))

    @classmethod
    def _do_write_variant(cls, project, bucket):
        layout = schema2_project_dataset_layout(project)
        gpf_instance = project.get_gpf_instance()
        ParquetWriter.write_variants(
            layout.study,
            project.get_variant_loader(
                bucket, gpf_instance.reference_genome),
            cls._get_partition_description(project),
            bucket,
            project,
            S2VariantsWriter)

    @classmethod
    def _variant_partitions(cls, project):
        part_desc = cls._get_partition_description(project)
        chromosome_lengths = dict(
            project.get_gpf_instance().reference_genome.get_all_chrom_lengths()
        )
        sum_parts, fam_parts = \
            part_desc.get_variant_partitions(chromosome_lengths)
        for part in sum_parts:
            yield part_desc.partition_directory("summary", part), part
        for part in fam_parts:
            yield part_desc.partition_directory("family", part), part

    @classmethod
    def _merge_parquets(cls, project, out_dir, partitions):
        layout = schema2_project_dataset_layout(project)
        full_out_dir = fs_utils.join(layout.study, out_dir)
        ParquetWriter.merge_parquets(
            cls._get_partition_description(project), full_out_dir, partitions
        )

    def _build_all_parquet_tasks(self, project, graph):
        pedigree_task = graph.create_task(
            "Generating Pedigree", self._do_write_pedigree, [project], [],
            input_files=[project.get_pedigree_filename()]
        )

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
        return [pedigree_task, all_parquet_task]

    def generate_import_task_graph(self, project) -> TaskGraph:
        graph = TaskGraph()
        if project.get_processing_parquet_dataset_dir() is None:
            self._build_all_parquet_tasks(project, graph)

        return graph
