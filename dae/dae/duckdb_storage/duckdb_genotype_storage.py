import logging
from typing import Any, cast, Optional
from contextlib import closing

import duckdb
from cerberus import Validator

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
            "type": "string", "required": True
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
        db_name = self.storage_config["db"]
        self.connection = duckdb.connect(f"{db_name}")
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
        return self.storage_config["bigquery"]["db"]

    @staticmethod
    def _create_table_layout(study_id: str) -> Schema2DatasetLayout:
        return Schema2DatasetLayout(
            study_id,
            f"{study_id}_pedigree",
            f"{study_id}_summary", f"{study_id}_family",
            f"{study_id}_meta")

    def _create_table(self, parquet_path, table_name):
        assert self.connection is not None

        query = f"CREATE TABLE {table_name} AS " \
            f"SELECT * FROM parquet_scan('{parquet_path}')"
        self.connection.sql(query)

    def _create_table_partitioned(
            self, parquet_path, table_name, partition):
        assert self.connection is not None
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
        tables_layout = self._create_table_layout(study_id)

        with closing(self.start()) as storage:
            storage._create_table(layout.meta, tables_layout.meta)
            storage._create_table(layout.pedigree, tables_layout.pedigree)
            storage._create_table_partitioned(
                layout.summary, tables_layout.summary,
                partition_descriptor.dataset_summary_partition())
            storage._create_table_partitioned(
                layout.family, tables_layout.family,
                partition_descriptor.dataset_family_partition())
        return tables_layout

    def build_backend(self, study_config, genome, gene_models):
        tables_layout = self._create_table_layout(study_config.id)
        return DuckDbVariants(
            self.storage_config["db"],
            tables_layout.family,
            tables_layout.summary,
            tables_layout.pedigree,
            tables_layout.meta,
            gene_models)
