import logging
from typing import cast

from dae.configuration.study_config_builder import StudyConfigBuilder
from dae.import_tools.import_tools import ImportProject, save_study_config
from dae.task_graph.graph import TaskGraph
from dae.schema2_storage.schema2_import_storage import Schema2ImportStorage, \
    schema2_dataset_layout

from impala_storage.schema2.impala2_genotype_storage import \
    HdfsStudyLayout, Impala2GenotypeStorage


logger = logging.getLogger(__file__)


class Impala2ImportStorage(Schema2ImportStorage):
    """Import logic for data in the Impala Schema 2 format."""

    @classmethod
    def _do_load_in_hdfs(cls, project: ImportProject) -> HdfsStudyLayout:
        genotype_storage = project.get_genotype_storage()
        assert isinstance(genotype_storage, Impala2GenotypeStorage)
        layout = schema2_dataset_layout(project.get_parquet_dataset_dir())
        return genotype_storage.hdfs_upload_dataset(
            project.study_id,
            layout.study,
            layout.pedigree,
            layout.meta)

    @classmethod
    def _do_load_in_impala(
        cls, project: ImportProject, hdfs_study_layout: HdfsStudyLayout
    ) -> None:
        genotype_storage = project.get_genotype_storage()
        assert isinstance(genotype_storage, Impala2GenotypeStorage)

        logger.info("HDFS study layout: %s", hdfs_study_layout)

        partition_description = cls._get_partition_description(project)
        genotype_storage.import_dataset(
            project.study_id,
            hdfs_study_layout,
            partition_description=partition_description,
        )

    @classmethod
    def _do_study_config(cls, project: ImportProject) -> None:
        genotype_storage: Impala2GenotypeStorage = \
            cast(Impala2GenotypeStorage, project.get_genotype_storage())
        # pylint: disable=protected-access
        pedigree_table = genotype_storage\
            ._construct_pedigree_table(project.study_id)
        summary_table, family_table = genotype_storage\
            ._construct_variant_tables(project.study_id)
        meta_table = genotype_storage\
            ._construct_metadata_table(project.study_id)

        variants_types = project.get_variant_loader_types()
        study_config = {
            "id": project.study_id,
            "conf_dir": ".",
            "has_denovo": project.has_denovo_variants(),
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
            storage_config = cast(dict, study_config["genotype_storage"])
            storage_config["tables"]["summary"] = summary_table
            storage_config["tables"]["family"] = family_table
            storage_config["tables"]["meta"] = meta_table
            genotype_browser = cast(dict, study_config["genotype_browser"])
            genotype_browser["enabled"] = True

        config_builder = StudyConfigBuilder(study_config)
        config = config_builder.build_config()

        save_study_config(
            project.get_gpf_instance().dae_config,
            project.study_id,
            config)

    def generate_import_task_graph(self, project: ImportProject) -> TaskGraph:
        graph = TaskGraph()
        all_parquet_tasks = []
        if project.get_processing_parquet_dataset_dir() is None:
            all_parquet_tasks = self._build_all_parquet_tasks(project, graph)

        if project.has_genotype_storage():
            hdfs_task = graph.create_task(
                "Copying to HDFS", self._do_load_in_hdfs,
                [project], all_parquet_tasks)

            impala_task = graph.create_task(
                "Importing into Impala", self._do_load_in_impala,
                [project, hdfs_task], [hdfs_task])
            graph.create_task(
                "Creating a study config", self._do_study_config,
                [project], [impala_task])

        return graph
