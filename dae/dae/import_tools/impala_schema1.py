import logging
import toml
from dae.utils import fs_utils
from dae.import_tools.parquet_writer import ParquetWriter
from dae.import_tools.import_tools import AbstractImportStorage
from dae.import_tools.task_graph import TaskGraph
from dae.backends.impala.parquet_io import NoPartitionDescriptor, \
    ParquetManager, ParquetPartitionDescriptor


logger = logging.getLogger(__file__)


class ImpalaSchema1ImportStorage(AbstractImportStorage):
    """Import logic for data in the Impala Schema 1 format."""

    def __init__(self, project):
        super().__init__(project)
        self.project = project

    @staticmethod
    def _pedigree_dir(project):
        return fs_utils.join(project.work_dir, f"{project.study_id}_pedigree")

    @staticmethod
    def _variants_dir(project):
        return fs_utils.join(project.work_dir, f"{project.study_id}_variants")

    @staticmethod
    def _get_partition_description(project, out_dir=None):
        out_dir = out_dir if out_dir else project.work_dir
        config_dict = project.get_partition_description_dict()
        if config_dict is None:
            return NoPartitionDescriptor(out_dir)
        return ParquetPartitionDescriptor.from_dict(config_dict, out_dir)

    @classmethod
    def _do_write_pedigree(cls, project):
        out_dir = cls._pedigree_dir(project)
        ParquetWriter.write_pedigree(
            project.get_pedigree(), out_dir,
            cls._get_partition_description(project),
            ParquetManager(),
        )

    @classmethod
    def _do_write_variant(cls, project, bucket):
        out_dir = cls._variants_dir(project)
        gpf_instance = project.get_gpf_instance()
        ParquetWriter.write_variant(
            project.get_variant_loader(bucket,
                                       gpf_instance.reference_genome),
            bucket,
            gpf_instance,
            project, cls._get_partition_description(project, out_dir),
            ParquetManager())

    @classmethod
    def _do_load_in_hdfs(cls, project):
        genotype_storage = project.get_genotype_storage()
        if genotype_storage is None or not genotype_storage.is_impala():
            logger.error("missing or non-impala genotype storage")
            return

        partition_description = cls._get_partition_description(project)

        pedigree_file = fs_utils.join(cls._pedigree_dir(project),
                                      "pedigree.parquet")
        genotype_storage.hdfs_upload_dataset(
            project.study_id,
            cls._variants_dir(project),
            pedigree_file,
            partition_description)

    @classmethod
    def _do_load_in_impala(cls, project):
        genotype_storage = project.get_genotype_storage()
        if genotype_storage is None or not genotype_storage.is_impala():
            logger.error("missing or non-impala genotype storage")
            return

        study_id = project.study_id

        hdfs_variants_dir = \
            genotype_storage.default_variants_hdfs_dirname(study_id)

        hdfs_pedigree_file = \
            genotype_storage.default_pedigree_hdfs_filename(project.study_id)

        logger.info("HDFS variants dir: %s", hdfs_variants_dir)
        logger.info("HDFS pedigree file: %s", hdfs_pedigree_file)

        partition_description = cls._get_partition_description(project)

        variants_schema_fn = fs_utils.join(
            cls._variants_dir(project), "_VARIANTS_SCHEMA")
        with open(variants_schema_fn) as infile:
            content = infile.read()
            schema = toml.loads(content)
            variants_schema = schema["variants_schema"]

        genotype_storage.impala_import_dataset(
            project.study_id,
            hdfs_pedigree_file,
            hdfs_variants_dir,
            partition_description=partition_description,
            variants_schema=variants_schema)

    def generate_import_task_graph(self) -> TaskGraph:
        graph = TaskGraph()
        pedigree_task = graph.create_task("ped task", self._do_write_pedigree,
                                          [self.project], [])

        bucket_tasks = []
        for bucket in self.project.get_import_variants_buckets():
            task = graph.create_task(f"Task {bucket}", self._do_write_variant,
                                     [self.project, bucket], [])
            bucket_tasks.append(task)

        if self.project.has_destination():
            hdfs_task = graph.create_task(
                "hdfs copy", self._do_load_in_hdfs,
                [self.project], [pedigree_task] + bucket_tasks)

            graph.create_task("impala import", self._do_load_in_impala,
                              [self.project], [hdfs_task])

        return graph
