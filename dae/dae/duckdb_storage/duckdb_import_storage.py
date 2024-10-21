import abc
import logging
import os
from contextlib import closing
from typing import Any, cast

import yaml

from dae.configuration.study_config_builder import StudyConfigBuilder
from dae.duckdb_storage.duckdb_genotype_storage import (
    DuckDbParquetStorage,
    DuckDbS3ParquetStorage,
    DuckDbStorage,
)
from dae.duckdb_storage.duckdb_legacy_genotype_storage import (
    DuckDbLegacyStorage,
)
from dae.duckdb_storage.duckdb_storage_helpers import (
    create_database_connection,
    create_duckdb_tables,
    create_relative_parquet_scans_layout,
    create_s3_filesystem,
)
from dae.import_tools.import_tools import ImportProject, save_study_config
from dae.schema2_storage.schema2_import_storage import (
    Schema2ImportStorage,
)
from dae.schema2_storage.schema2_layout import (
    Schema2DatasetLayout,
    load_schema2_dataset_layout,
)
from dae.task_graph.graph import TaskGraph
from dae.utils import fs_utils

logger = logging.getLogger(__name__)


class AbstractDuckDbImportStorage(Schema2ImportStorage, abc.ABC):
    """Import logic for data in the DuckDb Schema 2 format."""

    @staticmethod
    @abc.abstractmethod
    def _do_import_dataset(
        project: ImportProject,
    ) -> Schema2DatasetLayout:
        pass

    @classmethod
    def do_study_config(
        cls, project: ImportProject, study_tables: Schema2DatasetLayout,
    ) -> None:
        """Produce a study config for the given project."""
        genotype_storage = project.get_genotype_storage()
        if project.get_processing_parquet_dataset_dir() is not None:
            meta = cls.load_meta(project)
            study_config = yaml.safe_load(meta["study"])
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
                "tables": {
                    "pedigree": study_tables.pedigree,
                    "meta": study_tables.meta,
                },
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
                "Creating a study config", self.do_study_config,
                [project, tables_task], [tables_task])

        return graph


class DuckDbLegacyImportStorage(AbstractDuckDbImportStorage):
    """Import logic for data in the DuckDb Schema 2 format."""

    @classmethod
    def _do_import_dataset(
        cls, project: ImportProject,
    ) -> Schema2DatasetLayout:
        genotype_storage = project.get_genotype_storage()
        assert isinstance(
            genotype_storage,
            DuckDbLegacyStorage)
        layout = load_schema2_dataset_layout(
            project.get_parquet_dataset_dir(),
        )
        work_dir = project.work_dir

        return genotype_storage.import_dataset(
            work_dir,
            project.study_id,
            layout,
            project.get_partition_descriptor(),
        )


class DuckDbParquetImportStorage(AbstractDuckDbImportStorage):
    """Import logic for data in the DuckDb Schema 2 format."""

    @classmethod
    def _do_import_dataset(
        cls, project: ImportProject,
    ) -> Schema2DatasetLayout:
        genotype_storage = project.get_genotype_storage()
        assert isinstance(
            genotype_storage,
            DuckDbParquetStorage)
        layout = load_schema2_dataset_layout(
            project.get_parquet_dataset_dir(),
        )
        dest_layout = create_relative_parquet_scans_layout(
            str(genotype_storage.config.base_dir),
            project.study_id,
            project.get_partition_descriptor(),
        )
        fs_utils.copy(dest_layout.study, layout.study)
        return dest_layout


class DuckDbS3ParquetImportStorage(AbstractDuckDbImportStorage):
    """Import logic for data in the DuckDb Schema 2 format."""

    @classmethod
    def _do_import_dataset(
        cls, project: ImportProject,
    ) -> Schema2DatasetLayout:
        genotype_storage = project.get_genotype_storage()
        assert isinstance(
            genotype_storage,
            DuckDbS3ParquetStorage)
        layout = load_schema2_dataset_layout(
            project.get_parquet_dataset_dir(),
        )
        dest_layout = create_relative_parquet_scans_layout(
            str(genotype_storage.config.bucket_url),
            project.study_id,
            project.get_partition_descriptor(),
        )
        s3_fs = create_s3_filesystem(genotype_storage.config.endpoint_url)
        s3_fs.put(layout.study, dest_layout.study, recursive=True)

        return dest_layout


class DuckDbImportStorage(AbstractDuckDbImportStorage):
    """Import logic for data in the DuckDb Schema 2 format."""

    @classmethod
    def _do_import_dataset(
        cls, project: ImportProject,
    ) -> Schema2DatasetLayout:
        genotype_storage = project.get_genotype_storage()
        assert isinstance(
            genotype_storage,
            DuckDbStorage)
        layout = load_schema2_dataset_layout(
            project.get_parquet_dataset_dir(),
        )
        work_dir = project.work_dir
        work_db_filename = os.path.join(
            work_dir, genotype_storage.config.db)
        with closing(create_database_connection(
                work_db_filename, read_only=False),
            ) as connection:
            work_tables = create_duckdb_tables(
                connection,
                project.study_id,
                layout,
                project.get_partition_descriptor(),
            )

        db_filename = genotype_storage.get_db_filename()
        if not os.path.exists(db_filename):
            logger.warning(
                "replacing existing DuckDb database: %s",
                db_filename)

        # this could replace already existing database so we need
        # to shut down the genotype storage
        # reconnect the storage
        if genotype_storage.connection_factory is not None:
            genotype_storage.shutdown()
        assert genotype_storage.connection_factory is None

        fs_utils.copy(db_filename, work_db_filename)

        return work_tables
