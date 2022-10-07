import logging
from typing import cast

from dae.utils import fs_utils
from dae.configuration.study_config_builder import StudyConfigBuilder
from dae.impala_storage.schema1.import_commons import save_study_config
from dae.import_tools.parquet_writer import ParquetWriter
from dae.import_tools.import_tools import ImportStorage
from dae.import_tools.task_graph import TaskGraph
from dae.impala_storage.schema2.schema2_genotype_storage import \
    Schema2GenotypeStorage
from dae.parquet.schema2.parquet_io import NoPartitionDescriptor, \
    ParquetManager, ParquetPartitionDescriptor


logger = logging.getLogger(__file__)


class Schema2ImportStorage(ImportStorage):
    """Import logic for data in the Impala Schema 1 format."""

    @staticmethod
    def _pedigree_dir(project):
        return fs_utils.join(project.work_dir, f"{project.study_id}_pedigree")

    @staticmethod
    def _variants_dir(project):
        return fs_utils.join(project.work_dir, f"{project.study_id}_variants")

    @classmethod
    def _meta_dir(cls, project):
        return cls._variants_dir(project)

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
        assert isinstance(genotype_storage, Schema2GenotypeStorage)

        partition_description = cls._get_partition_description(project)

        pedigree_file = fs_utils.join(cls._pedigree_dir(project),
                                      "pedigree.parquet")
        meta_file = fs_utils.join(cls._meta_dir(project), "meta.parquet")
        return genotype_storage.hdfs_upload_dataset(
            project.study_id,
            cls._variants_dir(project),
            pedigree_file,
            meta_file,
            partition_description)

    @classmethod
    def _do_load_in_impala(cls, project, hdfs_study_layout):
        genotype_storage = project.get_genotype_storage()
        assert isinstance(genotype_storage, Schema2GenotypeStorage)

        logger.info("HDFS study layout: %s", hdfs_study_layout)

        partition_description = cls._get_partition_description(project)
        genotype_storage.import_dataset(
            project.study_id,
            hdfs_study_layout,
            partition_description=partition_description,
        )

    @classmethod
    def _do_study_config(cls, project):
        genotype_storage: Schema2GenotypeStorage = \
            cast(Schema2GenotypeStorage, project.get_genotype_storage())
        # pylint: disable=protected-access
        pedigree_table = genotype_storage\
            ._construct_pedigree_table(project.study_id)
        summary_table, family_table = genotype_storage\
            ._construct_variant_tables(project.study_id)
        meta_table = genotype_storage\
            ._construct_metadata_table(project.study_id)

        variants_types = project.get_import_variants_types()
        study_config = {
            "id": project.study_id,
            "conf_dir": ".",
            "has_denovo": "denovo" in variants_types,
            "has_cnv": "cnv" in variants_types,
            "has_transmitted": bool({"dae", "vcf"} & variants_types),
            "genotype_storage": {
                "id": genotype_storage.storage_id,
                "tables": {"pedigree": pedigree_table},
            },
            "genotype_browser": {"enabled": False},
        }

        if summary_table:
            assert family_table is not None
            storage_config = study_config["genotype_storage"]
            storage_config["tables"]["summary"] = summary_table
            storage_config["tables"]["family"] = family_table
            storage_config["tables"]["meta"] = meta_table
            study_config["genotype_browser"]["enabled"] = True

        config_builder = StudyConfigBuilder(study_config)
        config = config_builder.build_config()

        save_study_config(
            project.get_gpf_instance().dae_config,
            project.study_id,
            config, force=True)

    def generate_import_task_graph(self, project) -> TaskGraph:
        graph = TaskGraph()
        pedigree_task = graph.create_task("ped task", self._do_write_pedigree,
                                          [project], [])

        bucket_tasks = []
        for bucket in project.get_import_variants_buckets():
            task = graph.create_task(f"Task {bucket}", self._do_write_variant,
                                     [project, bucket], [])
            bucket_tasks.append(task)

        if project.has_destination():
            hdfs_task = graph.create_task(
                "hdfs copy", self._do_load_in_hdfs,
                [project], [pedigree_task] + bucket_tasks)

            impala_task = graph.create_task(
                "impala import", self._do_load_in_impala,
                [project, hdfs_task], [hdfs_task])
            graph.create_task(
                "study config", self._do_study_config,
                [project], [impala_task])

        return graph
