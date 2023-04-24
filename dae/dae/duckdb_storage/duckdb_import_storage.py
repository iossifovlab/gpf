from typing import cast

from dae.configuration.study_config_builder import StudyConfigBuilder
from dae.impala_storage.schema1.import_commons import save_study_config

from dae.task_graph.graph import TaskGraph
from dae.schema2_storage.schema2_import_storage import Schema2ImportStorage, \
    schema2_dataset_layout
from dae.duckdb_storage.duckdb_genotype_storage import DuckDbGenotypeStorage


class DuckDbImportStorage(Schema2ImportStorage):
    """Import logic for data in the DuckDb Schema 2 format."""

    @classmethod
    def _do_create_tables(cls, project):
        genotype_storage = project.get_genotype_storage()
        assert isinstance(genotype_storage, DuckDbGenotypeStorage)
        layout = schema2_dataset_layout(project.get_parquet_dataset_dir())
        return genotype_storage.import_dataset(
            project.study_id, layout, project.get_partition_descriptor())

    @classmethod
    def _do_study_config(cls, project):
        genotype_storage: DuckDbGenotypeStorage = \
            cast(DuckDbGenotypeStorage, project.get_genotype_storage())
        # pylint: disable=protected-access
        study_tables = genotype_storage._create_table_layout(project.study_id)

        variants_types = project.get_variant_loader_types()
        study_config = {
            "id": project.study_id,
            "conf_dir": ".",
            "has_denovo": "denovo" in variants_types,
            "has_cnv": "cnv" in variants_types,
            "has_transmitted": bool({"dae", "vcf"} & variants_types),
            "genotype_storage": {
                "id": genotype_storage.storage_id,
                "tables": {"pedigree": study_tables.pedigree},
            },
            "genotype_browser": {"enabled": False},
        }

        if study_tables.summary:
            assert study_tables.family is not None
            storage_config = study_config["genotype_storage"]
            storage_config["tables"]["summary"] = study_tables.summary
            storage_config["tables"]["family"] = study_tables.family
            storage_config["tables"]["meta"] = study_tables.meta
            study_config["genotype_browser"]["enabled"] = True

        config_builder = StudyConfigBuilder(study_config)
        config = config_builder.build_config()

        save_study_config(
            project.get_gpf_instance().dae_config,
            project.study_id,
            config, force=True)

    def generate_import_task_graph(self, project) -> TaskGraph:
        graph = TaskGraph()
        all_parquet_tasks = []
        if project.get_processing_parquet_dataset_dir() is None:
            all_parquet_tasks = self._build_all_parquet_tasks(project, graph)

        if project.has_genotype_storage():
            tables_task = graph.create_task(
                "Create DuckDb Tables", self._do_create_tables,
                [project], all_parquet_tasks)

            graph.create_task(
                "Creating a study config", self._do_study_config,
                [project], [tables_task])

        return graph
