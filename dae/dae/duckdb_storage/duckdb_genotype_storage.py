from __future__ import annotations

import os
import re
import logging
from typing import Any, cast, Optional
from contextlib import closing

import duckdb
from cerberus import Validator

from dae.utils import fs_utils
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genomic_resources.gene_models import GeneModels

from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.schema2_storage.schema2_import_storage import Schema2DatasetLayout
from dae.duckdb_storage.duckdb_variants import DuckDbVariants

logger = logging.getLogger(__name__)


def _duckdb_global_connect() -> duckdb.DuckDBPyConnection:
    logger.info("connection to gloabl duckdb")
    return cast(duckdb.DuckDBPyConnection, duckdb)


def _duckdb_db_connect(
    db_name: str, read_only: bool = True
) -> duckdb.DuckDBPyConnection:
    logger.debug("duckdb internal connection to %s", db_name)
    return duckdb.connect(db_name, read_only=read_only)


def duckdb_connect(
    db_name: Optional[str] = None, read_only: bool = True
) -> duckdb.DuckDBPyConnection:
    if db_name is not None:
        return _duckdb_db_connect(db_name=db_name, read_only=read_only)
    return _duckdb_global_connect()


class DuckDbGenotypeStorage(GenotypeStorage):
    """Defines DuckDb genotype storage."""

    VALIDATION_SCHEMA = {
        "storage_type": {"type": "string", "allowed": ["duckdb"]},
        "id": {
            "type": "string", "required": True
        },
        "db": {
            "type": "string",
        },
        "read_only": {
            "type": "boolean",
            "default": False,
        },
        "studies_dir": {
            "type": "string",
        },
        "base_dir": {
            "type": "string",
        }
    }

    def __init__(self, storage_config: dict[str, Any]):
        super().__init__(storage_config)
        self.connection_factory: Optional[duckdb.DuckDBPyConnection] = None

    @classmethod
    def validate_and_normalize_config(cls, config: dict) -> dict:
        config = super().validate_and_normalize_config(config)
        validator = Validator(cls.VALIDATION_SCHEMA)
        if not validator.validate(config):
            logger.error(
                "wrong config format for duckdb genotype storage: %s",
                validator.errors)
            raise ValueError(
                f"wrong config format for duckdb storage: "
                f"{validator.errors}")
        result = cast(dict, validator.document)
        base_dir = result.get("base_dir")
        if base_dir:
            if not os.path.isabs(base_dir):
                raise ValueError(
                    f"DuckDb genotype storage base dir should be an "
                    f"absolute path; <{base_dir}> passed instead.")
        return result

    @classmethod
    def get_storage_type(cls) -> str:
        return "duckdb"

    def start(self) -> DuckDbGenotypeStorage:
        if self.connection_factory:
            logger.warning(
                "starting already started DuckDb genotype storage: <%s>",
                self.storage_id)
            return self

        db_name = self.get_db()
        read_only = self.get_read_only()
        if db_name is not None:
            db_name = self._base_dir_join(db_name)
            dirname = os.path.dirname(db_name)
            os.makedirs(dirname, exist_ok=True)

        self.connection_factory = duckdb_connect(
            db_name=db_name, read_only=read_only)
        return self

    def shutdown(self) -> DuckDbGenotypeStorage:
        if self.connection_factory is None:
            logger.warning(
                "trying to shutdown already stopped DuckDbGenotypeStorage")
            return self
        self.connection_factory.close()
        self.connection_factory = None
        return self

    def close(self) -> None:
        pass
        # self.shutdown()

    def get_base_dir(self) -> Optional[str]:
        return self.storage_config.get("base_dir")

    def get_db(self) -> Optional[str]:
        return self.storage_config.get("db")

    def get_read_only(self) -> bool:
        return cast(bool, self.storage_config.get("read_only", True))

    def get_studies_dir(self) -> Optional[str]:
        return self.storage_config.get("studies_dir")

    @staticmethod
    def create_table_layout(study_id: str) -> Schema2DatasetLayout:
        return Schema2DatasetLayout(
            study_id,
            f"{study_id}_pedigree",
            f"{study_id}_summary", f"{study_id}_family",
            f"{study_id}_meta")

    def create_parquet_scans_layout_from_studies_dir(
            self,
            study_id: str,
            partition_descriptor: PartitionDescriptor,
            studies_dir: str) -> Schema2DatasetLayout:
        """Construct DuckDb parquet scans for all studies tables."""
        study_dir = fs_utils.join(studies_dir, study_id)
        pedigree_path = fs_utils.join(study_dir, "pedigree")
        meta_path = fs_utils.join(study_dir, "meta")
        summary_path = fs_utils.join(study_dir, "summary")
        summary_partition = partition_descriptor.dataset_summary_partition()
        family_path = fs_utils.join(study_dir, "family")
        family_partition = partition_descriptor.dataset_family_partition()
        study_dir = self._base_dir_join(study_dir)
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

    @staticmethod
    def create_parquet_scans_layout_from_layout(
            layout: Schema2DatasetLayout,
            partition_descriptor: PartitionDescriptor) -> Schema2DatasetLayout:
        """Construct DuckDb parquet scans for all studies tables."""
        summary_partition = partition_descriptor.dataset_summary_partition()
        family_partition = partition_descriptor.dataset_family_partition()
        paths = Schema2DatasetLayout(
            layout.study,
            f"{layout.pedigree}",
            f"{layout.summary}/{'*/' * len(summary_partition)}*.parquet",
            f"{layout.family}/{'*/' * len(family_partition)}*.parquet",
            f"{layout.meta}")
        return Schema2DatasetLayout(
            paths.study,
            f"parquet_scan('{paths.pedigree}')",
            f"parquet_scan('{paths.summary}')",
            f"parquet_scan('{paths.family}')",
            f"parquet_scan('{paths.meta}')")

    def _create_table(self, parquet_path: str, table_name: str) -> None:
        assert self.connection_factory is not None
        with self.connection_factory.cursor() as connection:
            assert connection is not None
            query = f"DROP TABLE IF EXISTS {table_name}"
            connection.sql(query)

            query = f"CREATE TABLE {table_name} AS " \
                f"SELECT * FROM parquet_scan('{parquet_path}')"
            connection.sql(query)

    def _create_table_partitioned(
            self, parquet_path: str, table_name: str,
            partition: list[tuple[str, str]]) -> None:
        assert self.connection_factory is not None
        with self.connection_factory.cursor() as connection:
            query = f"DROP TABLE IF EXISTS {table_name}"
            connection.sql(query)

            dataset_path = f"{parquet_path}/{ '*/' * len(partition)}*.parquet"
            query = f"CREATE TABLE {table_name} AS " \
                f"SELECT * FROM " \
                f"parquet_scan('{dataset_path}', hive_partitioning = 1)"
            connection.sql(query)

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
                if layout.summary is None:
                    assert layout.family is None
                    tables_layout = Schema2DatasetLayout(
                        tables_layout.study,
                        tables_layout.pedigree,
                        None,
                        None,
                        tables_layout.meta)
                else:
                    assert tables_layout.summary is not None
                    assert tables_layout.family is not None
                    assert layout.summary is not None
                    assert layout.family is not None
                    storage._create_table_partitioned(
                        layout.summary, tables_layout.summary,
                        partition_descriptor.dataset_summary_partition())
                    storage._create_table_partitioned(
                        layout.family, tables_layout.family,
                        partition_descriptor.dataset_family_partition())
            return tables_layout

        if self.get_studies_dir() is not None:
            # copy parquet files
            studies_dir = self.get_studies_dir()
            assert studies_dir is not None

            dest_layout = self.create_parquet_scans_layout_from_studies_dir(
                study_id, partition_descriptor,
                studies_dir=studies_dir)

            fs_utils.copy(dest_layout.study, layout.study)
            return dest_layout

        if self.get_studies_dir() is None:
            return self.create_parquet_scans_layout_from_layout(
                layout, partition_descriptor)

        raise ValueError(
            f"bad DuckDb genotype storage configuration: "
            f"{self.storage_config}")

    PARQUET_SCAN = re.compile(r"parquet_scan\('(?P<parquet_path>.+)'\)")

    def _base_dir_join(self, dir_name: str) -> str:
        base_dir = self.get_base_dir()
        if base_dir is None:
            return dir_name
        return fs_utils.join(base_dir, dir_name)

    def _base_dir_join_parquet_scan_or_table(
            self, parquet_scan: Optional[str]) -> Optional[str]:
        if parquet_scan is None:
            return None
        if self.get_base_dir() is None:
            return parquet_scan

        match = self.PARQUET_SCAN.fullmatch(parquet_scan)
        if not match:
            return parquet_scan

        parquet_path = match.groupdict()["parquet_path"]
        assert parquet_path
        base_dir = self.get_base_dir()
        assert base_dir is not None

        full_path = fs_utils.join(base_dir, parquet_path)
        return f"parquet_scan('{full_path}')"

    def build_backend(
            self, study_config: dict,
            genome: ReferenceGenome,
            gene_models: GeneModels) -> DuckDbVariants:
        tables = study_config["genotype_storage"]["tables"]
        pedigree = self._base_dir_join_parquet_scan_or_table(
            tables["pedigree"])
        assert pedigree is not None
        meta = self._base_dir_join_parquet_scan_or_table(tables["meta"])
        assert meta is not None

        tables_layout = Schema2DatasetLayout(
            study_config["id"],
            pedigree,
            self._base_dir_join_parquet_scan_or_table(tables.get("summary")),
            self._base_dir_join_parquet_scan_or_table(tables.get("family")),
            meta)

        db_name = self.get_db()
        if db_name is not None:
            db_name = self._base_dir_join(db_name)

        if self.connection_factory is None:
            raise ValueError(
                f"duckdb genotype storage not started: "
                f"{self.storage_config}")
        assert self.connection_factory is not None
        return DuckDbVariants(
            self.connection_factory,
            db_name,
            tables_layout.family,
            tables_layout.summary,
            tables_layout.pedigree,
            tables_layout.meta,
            gene_models)
