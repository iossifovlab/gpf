from __future__ import annotations

import abc
import logging
import pathlib
from typing import Any

import duckdb

from dae.duckdb_storage.duckdb2_variants import (
    Db2Layout,
    DuckDb2Variants,
    DuckDbConnectionFactory,
)
from dae.duckdb_storage.duckdb_storage_config import (
    DuckDbConf,
    DuckDbParquetConf,
    DuckDbS3ParquetConf,
    parse_duckdb_config,
)
from dae.duckdb_storage.duckdb_storage_helpers import (
    create_database_connection,
    create_memory_connection,
    create_s3_secret_clause,
    create_study_parquet_tables_layout,
    get_study_config_tables,
)
from dae.genomic_resources.gene_models import GeneModels
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genotype_storage.genotype_storage import GenotypeStorage

logger = logging.getLogger(__name__)


class AbstractDuckDbStorage(GenotypeStorage, DuckDbConnectionFactory):
    """Defines abstract DuckDb genotype storage."""

    def __init__(
        self,
        dd_config: DuckDbConf | DuckDbParquetConf | DuckDbS3ParquetConf,
    ):
        super().__init__(dd_config.model_dump())
        self.dd_config = dd_config
        self.connection_factory: duckdb.DuckDBPyConnection | None = None

    def is_read_only(self) -> bool:
        return True

    def shutdown(self) -> AbstractDuckDbStorage:
        if self.connection_factory is None:
            logger.warning(
                "trying to shutdown already stopped "
                "DuckDb Storage")
            return self
        self.connection_factory.close()
        self.connection_factory = None
        return self

    def connect(self) -> duckdb.DuckDBPyConnection:
        if self.connection_factory is None:
            self.start()
        assert self.connection_factory is not None
        return self.connection_factory

    @abc.abstractmethod
    def build_study_layout(
        self,
        study_config: dict[str, Any],
    ) -> Db2Layout:
        """Construct study layout from study and storage configuration."""

    def build_backend(
            self, study_config: dict,
            genome: ReferenceGenome,
            gene_models: GeneModels) -> DuckDb2Variants:
        if self.connection_factory is None:
            self.start()

        tables_layout = self.build_study_layout(study_config)

        if self.connection_factory is None:
            raise ValueError(
                f"duckdb genotype storage not started: "
                f"{self.storage_config}")
        assert self.connection_factory is not None

        return DuckDb2Variants(
            self,
            tables_layout,
            gene_models,
            genome,
        )


class DuckDbParquetStorage(AbstractDuckDbStorage):
    """Defines `duckdb_parquet` genotype storage."""

    def __init__(self, dd_config: DuckDbParquetConf):
        super().__init__(dd_config)
        self.config = dd_config
        self.connection_factory: duckdb.DuckDBPyConnection | None = None

    def start(self) -> DuckDbParquetStorage:
        if self.connection_factory:
            logger.warning(
                "starting already started DuckDb genotype storage: <%s>",
                self.storage_id)
            return self

        logger.info("connection to inmemory duckdb")
        self.connection_factory = create_memory_connection(
            memory_limit=self.config.memory_limit)

        return self

    @classmethod
    def get_storage_types(cls) -> set[str]:
        return {"duckdb_parquet"}

    def build_study_layout(
        self,
        study_config: dict[str, Any],
    ) -> Db2Layout:
        base_url = str(self.config.base_dir)
        return create_study_parquet_tables_layout(study_config, base_url)


def duckdb_parquet_storage_factory(
    storage_config: dict[str, Any],
) -> DuckDbParquetStorage:
    """Create `duckdb_parquet` genotype storage."""
    dd_config = parse_duckdb_config(storage_config)
    if dd_config.storage_type != "duckdb_parquet":
        raise TypeError(
            f"unexpected storage type: {dd_config.storage_type}")
    return DuckDbParquetStorage(dd_config)


class DuckDbS3ParquetStorage(AbstractDuckDbStorage):
    """Defines `duckdb_s3_parquet` genotype storage."""

    def __init__(self, dd_config: DuckDbS3ParquetConf):
        super().__init__(dd_config)
        self.config = dd_config
        self.connection_factory: duckdb.DuckDBPyConnection | None = None

    def start(self) -> DuckDbS3ParquetStorage:
        if self.connection_factory:
            logger.warning(
                "starting already started DuckDb genotype storage: <%s>",
                self.storage_id)
            return self

        logger.info("connection to inmemory duckdb")
        self.connection_factory = create_memory_connection(
            memory_limit=self.config.memory_limit)

        s3_secret_clause = create_s3_secret_clause(
            self.storage_id, self.config.endpoint_url)
        self.connection_factory.sql(s3_secret_clause)

        return self

    @classmethod
    def get_storage_types(cls) -> set[str]:
        return {"duckdb_s3_parquet"}

    def build_study_layout(
        self,
        study_config: dict[str, Any],
    ) -> Db2Layout:
        base_url = str(self.config.bucket_url)
        return create_study_parquet_tables_layout(study_config, base_url)


def duckdb_s3_parquet_storage_factory(
    storage_config: dict[str, Any],
) -> DuckDbS3ParquetStorage:
    """Create `duckdb_s3_parquet` genotype storage."""
    dd_config = parse_duckdb_config(storage_config)
    if dd_config.storage_type != "duckdb_s3_parquet":
        raise TypeError(
            f"unexpected storage type: {dd_config.storage_type}")
    return DuckDbS3ParquetStorage(dd_config)


class DuckDbStorage(AbstractDuckDbStorage):
    """Defines `duckdb` genotype storage."""

    def __init__(self, dd_config: DuckDbConf):
        super().__init__(dd_config)
        self.config = dd_config
        self.connection_factory: duckdb.DuckDBPyConnection | None = None

    @classmethod
    def get_storage_types(cls) -> set[str]:
        return {"duckdb"}

    def start(self) -> DuckDbStorage:
        if self.connection_factory:
            logger.warning(
                "starting already started DuckDb genotype storage: <%s>",
                self.storage_id)
            return self
        db_filename = self.get_db_filename()
        self.connection_factory = create_database_connection(
            db_filename,
            read_only=True,
            memory_limit=self.config.memory_limit)
        return self

    def get_db_filename(self) -> str:
        """Construct database full filename."""
        db = self.config.db
        if db.is_absolute():
            return str(db)
        return str(self.config.base_dir / db)

    def build_study_layout(
        self,
        study_config: dict[str, Any],
    ) -> Db2Layout:
        db_name = pathlib.Path(self.get_db_filename()).stem
        study_config_layout = get_study_config_tables(
            study_config, db_name=db_name)
        return Db2Layout(
            db=db_name,
            study=study_config_layout.study,
            pedigree=study_config_layout.pedigree,
            summary=study_config_layout.summary,
            family=study_config_layout.family,
            meta=study_config_layout.meta,
        )


def duckdb_storage_factory(
    storage_config: dict[str, Any],
) -> DuckDbStorage:
    """Create `duckdb` genotype storage."""
    dd_config = parse_duckdb_config(storage_config)
    if dd_config.storage_type != "duckdb":
        raise TypeError(
            f"unexpected storage type: {dd_config.storage_type}")
    return DuckDbStorage(dd_config)
