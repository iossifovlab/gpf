import logging
import time

import toml

from dae.configuration.study_config_builder import StudyConfigBuilder
from dae.utils import fs_utils
from dae.backends.impala.import_commons import save_study_config
from dae.import_tools.parquet_writer import ParquetWriter
from dae.import_tools.import_tools import ImportStorage
from dae.import_tools.task_graph import TaskGraph
from dae.backends.impala.parquet_io import NoPartitionDescriptor, \
    ParquetManager, ParquetPartitionDescriptor


logger = logging.getLogger(__file__)


class ImpalaSchema1ImportStorage(ImportStorage):
    """Import logic for data in the Impala Schema 1 format."""

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
        start = time.time()
        out_dir = cls._pedigree_dir(project)
        ParquetWriter.write_pedigree(
            project.get_pedigree(), out_dir,
            cls._get_partition_description(project),
            ParquetManager(),
        )
        elapsed = time.time() - start
        logger.info("prepare pedigree elapsed %.2f sec", elapsed)
        project.stats[("elapsed", "pedigree")] = elapsed

    @classmethod
    def _do_write_variant(cls, project, bucket):
        start = time.time()
        out_dir = cls._variants_dir(project)
        gpf_instance = project.get_gpf_instance()
        ParquetWriter.write_variant(
            project.get_variant_loader(bucket,
                                       gpf_instance.reference_genome),
            bucket,
            gpf_instance,
            project, cls._get_partition_description(project, out_dir),
            ParquetManager())
        elapsed = time.time() - start
        logger.info(
            "prepare variants for bucket %s elapsed %.2f sec",
            bucket, elapsed)
        project.stats[("elapsed", f"variants {bucket}")] = elapsed

    @classmethod
    def _do_load_in_hdfs(cls, project):
        start = time.time()
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
        elapsed = time.time() - start
        logger.info("load in hdfs elapsed %.2f sec", elapsed)
        project.stats[("elapsed", "hdfs")] = elapsed

    @classmethod
    def _do_load_in_impala(cls, project):
        start = time.time()
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
        elapsed = time.time() - start
        logger.info("load in impala elapsed %.2f sec", elapsed)
        project.stats[("elapsed", "impala")] = elapsed

    @staticmethod
    def _construct_variants_table(study_id):
        return f"{study_id}_variants"

    @staticmethod
    def _construct_pedigree_table(study_id):
        return f"{study_id}_pedigree"

    @classmethod
    def _do_study_config(cls, project):
        start = time.time()
        pedigree_table = cls._construct_pedigree_table(project.study_id)
        study_config = {
            "id": project.study_id,
            "conf_dir": ".",
            "has_denovo": False,
            "genotype_storage": {
                "id": project.get_genotype_storage().storage_id,
                "tables": {"pedigree": pedigree_table},
            },
            "genotype_browser": {"enabled": False},
        }

        if project.has_variants():
            variants_table = cls._construct_variants_table(project.study_id)
            storage_config = study_config["genotype_storage"]
            storage_config["tables"]["variants"] = variants_table
            study_config["genotype_browser"]["enabled"] = True

        config_builder = StudyConfigBuilder(study_config)
        config = config_builder.build_config()

        save_study_config(
            project.get_gpf_instance().dae_config,
            project.study_id,
            config, force=True)
        elapsed = time.time() - start
        logger.info("study config elapsed %.2f sec", elapsed)
        project.stats[("elapsed", "study_config")] = elapsed

    def generate_import_task_graph(self, project) -> TaskGraph:
        graph = TaskGraph()
        pedigree_task = graph.create_task("ped task", self._do_write_pedigree,
                                          [project], [])

        bucket_tasks = []
        for bucket in project.get_import_variants_buckets():
            task = graph.create_task(f"Task {bucket}", self._do_write_variant,
                                     [project, bucket], [])
            bucket_tasks.append(task)

        if project.has_destination() or project.has_gpf_instance():
            hdfs_task = graph.create_task(
                "hdfs copy", self._do_load_in_hdfs,
                [project], [pedigree_task] + bucket_tasks)

            impala_task = graph.create_task(
                "impala import", self._do_load_in_impala,
                [project], [hdfs_task])

            graph.create_task(
                "study config", self._do_study_config,
                [project], [impala_task])
        return graph
