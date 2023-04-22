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
            project.study_id, layout)

    @classmethod
    def _do_study_config(cls, project):
        pass

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
