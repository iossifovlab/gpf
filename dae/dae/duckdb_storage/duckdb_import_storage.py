from typing import cast, Any

import yaml

from dae.configuration.study_config_builder import StudyConfigBuilder
from dae.import_tools.import_tools import save_study_config, ImportProject

from dae.task_graph.graph import TaskGraph
from dae.schema2_storage.schema2_import_storage import Schema2ImportStorage, \
    Schema2DatasetLayout, \
    schema2_dataset_layout
from dae.duckdb_storage.duckdb_genotype_storage import DuckDbGenotypeStorage


class DuckDbImportStorage(Schema2ImportStorage):
    """Import logic for data in the DuckDb Schema 2 format."""

    @classmethod
    def _do_import_dataset(
            cls, project: ImportProject) -> Schema2DatasetLayout:
        genotype_storage = project.get_genotype_storage()
        assert isinstance(genotype_storage, DuckDbGenotypeStorage)
        layout = schema2_dataset_layout(project.get_parquet_dataset_dir())
        return genotype_storage.import_dataset(
            project.study_id, layout, project.get_partition_descriptor())

    @classmethod
    def _do_study_config(
        cls, project: ImportProject, study_tables: Schema2DatasetLayout
    ) -> None:
        genotype_storage: DuckDbGenotypeStorage = \
            cast(DuckDbGenotypeStorage, project.get_genotype_storage())
        if project.get_processing_parquet_dataset_dir() is not None:
            meta = cls.load_meta(project)
            study_config = yaml.load(meta["study"], yaml.Loader)
            study_config["id"] = project.study_id
        else:
            variants_types = project.get_variant_loader_types()
            study_config = {
                "id": project.study_id,
                "conf_dir": ".",
                "has_denovo": project.has_denovo_variants(),
                "has_cnv": "cnv" in variants_types,
                "has_transmitted": bool({"dae", "vcf"} & variants_types),
            }
        study_config.update({
            "genotype_storage": {
                "id": genotype_storage.storage_id,
                "tables": {"pedigree": study_tables.pedigree},
            },
            "genotype_browser": {"enabled": False},
        })

        if study_tables.summary:
            assert study_tables.family is not None
            storage_config = cast(dict, study_config["genotype_storage"])
            tables_config = cast(dict[str, str], storage_config["tables"])
            tables_config["summary"] = study_tables.summary
            tables_config["family"] = study_tables.family
            tables_config["meta"] = study_tables.meta
            genotype_browser_config = \
                cast(dict[str, Any], study_config["genotype_browser"])
            genotype_browser_config["enabled"] = True

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
            tables_task = graph.create_task(
                "Create DuckDb import dataset", self._do_import_dataset,
                [project], all_parquet_tasks)

            graph.create_task(
                "Creating a study config", self._do_study_config,
                [project, tables_task], [tables_task])

        return graph
