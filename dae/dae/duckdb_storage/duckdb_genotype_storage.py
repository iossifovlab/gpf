import os
import logging
from typing import Any, cast, Optional
from contextlib import closing

import duckdb
from cerberus import Validator

from dae.utils import fs_utils
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.schema2_storage.schema2_import_storage import Schema2DatasetLayout
from dae.duckdb_storage.duckdb_variants import DuckDbVariants

logger = logging.getLogger(__name__)


class DuckDbGenotypeStorage(GenotypeStorage):
    """Defines Google Cloud Platform (GCP) genotype storage."""

    VALIDATION_SCHEMA = {
        "storage_type": {"type": "string", "allowed": ["duckdb"]},
        "id": {
            "type": "string", "required": True
        },
        "db": {
            "type": "string",
        },
        "studies_path": {
            "type": "string",
        },
    }

    def __init__(self, storage_config: dict[str, Any]):
        super().__init__(storage_config)
        self.connection: Optional[duckdb.DuckDBPyConnection] = None

    @classmethod
    def validate_and_normalize_config(cls, config: dict) -> dict:
        config = super().validate_and_normalize_config(config)
        validator = Validator(cls.VALIDATION_SCHEMA)
        if not validator.validate(config):
            logger.error(
                "wrong config format for impala genotype storage: %s",
                validator.errors)
            raise ValueError(
                f"wrong config format for impala storage: "
                f"{validator.errors}")
        return cast(dict, validator.document)

    @classmethod
    def get_storage_type(cls) -> str:
        return "duckdb"

    def start(self):
        if self.connection:
            logger.warning(
                "starting already started DuckDb genotype storage: <%s>",
                self.storage_id)
            return self
            # raise ValueError(
            #     f"already started DuckDb storage <{self.storage_id}>")
        if self.get_db() is not None:
            db_name = self.get_db()
            dirname = os.path.dirname(db_name)
            os.makedirs(dirname, exist_ok=True)
            self.connection = duckdb.connect(f"{db_name}")
            return self

        self.connection = duckdb.connect()
        return self

    def shutdown(self):
        if self.connection is None:
            logger.warning(
                "trying to shutdown already stopped DuckDbGenotypeStorage")
            return
        self.connection.close()
        self.connection = None

    def close(self):
        self.shutdown()

    def get_db(self):
        return self.storage_config.get("db")

    def get_studies_path(self):
        return self.storage_config.get("studies_path")

    @staticmethod
    def create_table_layout(study_id: str) -> Schema2DatasetLayout:
        return Schema2DatasetLayout(
            study_id,
            f"{study_id}_pedigree",
            f"{study_id}_summary", f"{study_id}_family",
            f"{study_id}_meta")

    @staticmethod
    def create_parquet_scans_layout(
            study_id: str,
            partition_descriptor: PartitionDescriptor,
            base_dir: Optional[str] = "") -> Schema2DatasetLayout:
        """Construct DuckDb parquet scans for all studies tables."""
        study_dir = fs_utils.join(base_dir, study_id)
        pedigree_path = fs_utils.join(study_dir, "pedigree")
        meta_path = fs_utils.join(study_dir, "meta")
        summary_path = fs_utils.join(study_dir, "summary")
        summary_partition = partition_descriptor.dataset_summary_partition()
        family_path = fs_utils.join(study_dir, "family")
        family_partition = partition_descriptor.dataset_family_partition()

        paths = Schema2DatasetLayout(
            study_dir,
            f"{pedigree_path}/pedigree.parquet",
            f"{summary_path}/{'*/' * len(summary_partition)}*.parquet",
            f"{family_path}/{'*/' * len(family_partition)}*.parquet",
            f"{meta_path}/meta.parquet")
        return Schema2DatasetLayout(
            study_dir,
            f"parquet_scan('{paths.pedigree}')",
            f"parquet_scan('{paths.summary}')",
            f"parquet_scan('{paths.family}')",
            f"parquet_scan('{paths.meta}')")

    def _create_table(self, parquet_path, table_name):
        assert self.connection is not None
        query = f"DROP TABLE IF EXISTS {table_name}"
        self.connection.sql(query)

        query = f"CREATE TABLE {table_name} AS " \
            f"SELECT * FROM parquet_scan('{parquet_path}')"
        self.connection.sql(query)

    def _create_table_partitioned(
            self, parquet_path, table_name, partition):
        assert self.connection is not None
        query = f"DROP TABLE IF EXISTS {table_name}"
        self.connection.sql(query)

        dataset_path = f"{parquet_path}/{ '*/' * len(partition)}*.parquet"
        query = f"CREATE TABLE {table_name} AS " \
            f"SELECT * FROM parquet_scan('{dataset_path}')"
        self.connection.sql(query)

    def import_dataset(
            self,
            study_id: str,
            layout: Schema2DatasetLayout,
            partition_descriptor: PartitionDescriptor) -> Schema2DatasetLayout:
        """Import study parquet dataset into duckdb genotype storage."""
        if self.get_db() is not None:
            tables_layout = self.create_table_layout(study_id)

            with closing(self.start()) as storage:
                # pylint: disable=protected-access
                storage._create_table(layout.meta, tables_layout.meta)
                storage._create_table(layout.pedigree, tables_layout.pedigree)
                storage._create_table_partitioned(
                    layout.summary, tables_layout.summary,
                    partition_descriptor.dataset_summary_partition())
                storage._create_table_partitioned(
                    layout.family, tables_layout.family,
                    partition_descriptor.dataset_family_partition())
            return tables_layout

        if self.get_studies_path() is not None:
            # copy parquet files
            dest_layout = self.create_parquet_scans_layout(
                study_id, partition_descriptor,
                base_dir=self.get_studies_path())
            fs_utils.copy(dest_layout.study, layout.study)
            return dest_layout

        raise ValueError(
            f"bad DuckDb genotype storage configuration: "
            f"{self.storage_config}")

    def build_backend(self, study_config, genome, gene_models):
        if self.get_db() is not None:
            tables_layout = self.create_table_layout(study_config.id)
        elif self.get_studies_path() is not None:

            tables_layout = self.create_parquet_scans_layout(
                study_config.id, PartitionDescriptor(),
                base_dir=self.get_studies_path())

            result = duckdb.sql(
                f"SELECT value FROM {tables_layout.meta} "
                f"WHERE key = 'partition_description'").fetchall()
            if len(result) >= 0:
                partition_descriptor = \
                    PartitionDescriptor.parse_string(result[0][0])
                tables_layout = self.create_parquet_scans_layout(
                    study_config.id, partition_descriptor,
                    base_dir=self.get_studies_path())
        else:
            raise ValueError(
                f"wrong DuckDb genotype storage configuration: "
                f"{self.storage_config}")

        return DuckDbVariants(
            self.get_db(),
            tables_layout.family,
            tables_layout.summary,
            tables_layout.pedigree,
            tables_layout.meta,
            gene_models)
