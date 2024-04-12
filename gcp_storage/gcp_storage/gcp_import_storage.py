import logging
from typing import cast, Any

from dae.configuration.study_config_builder import StudyConfigBuilder
from dae.import_tools.import_tools import ImportProject, save_study_config
from dae.task_graph.graph import TaskGraph
from dae.schema2_storage.schema2_import_storage import Schema2ImportStorage, \
    schema2_dataset_layout
from gcp_storage.gcp_genotype_storage import GcpGenotypeStorage


logger = logging.getLogger(__file__)


class GcpImportStorage(Schema2ImportStorage):
    """Import logic for data in the GCP Schema 2."""

    @classmethod
    def _do_import_dataset(cls, project: ImportProject) -> None:
        layout = schema2_dataset_layout(project.get_parquet_dataset_dir())
        genotype_storage = cast(
            GcpGenotypeStorage, project.get_genotype_storage())
        assert isinstance(genotype_storage, GcpGenotypeStorage)
        genotype_storage.gcp_import_dataset(
            project.study_id, layout)

    @classmethod
    def _do_study_config(cls, project: ImportProject) -> None:
        genotype_storage: GcpGenotypeStorage = \
            cast(GcpGenotypeStorage, project.get_genotype_storage())
        # pylint: disable=protected-access
        study_tables = genotype_storage._study_tables({"id": project.study_id})

        variants_types = project.get_variant_loader_types()
        study_config = {
            "id": project.study_id,
            "conf_dir": ".",
            "has_denovo": project.has_denovo_variants(),
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
            storage_config = cast(
                dict[str, Any], study_config["genotype_storage"])
            storage_config["tables"]["summary"] = study_tables.summary
            storage_config["tables"]["family"] = study_tables.family
            storage_config["tables"]["meta"] = study_tables.meta
            genotype_browser_config = cast(
                dict[str, Any], study_config["genotype_browser"])
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
            import_task = graph.create_task(
                "Import Dataset into GCP genotype storage",
                self._do_import_dataset,
                [project], all_parquet_tasks)

            graph.create_task(
                "Create study config",
                self._do_study_config,
                [project], [import_task])
        return graph
