from __future__ import annotations

import abc
import logging
import os
import pathlib
import re
import textwrap
import time
from contextlib import closing
from typing import Any, ClassVar, cast
from urllib.parse import urlparse

import duckdb
import jinja2
from cerberus import Validator
from s3fs.core import S3FileSystem

from dae.duckdb_storage.duckdb2_variants import (
    Db2Layout,
    DuckDb2Variants,
    DuckDbConnectionFactory,
)
from dae.duckdb_storage.duckdb_storage_config import (
    DuckDbConf,
    DuckDbParquetConf,
    DuckDbS3ParquetConf,
    S3Path,
    parse_duckdb_config,
)
from dae.duckdb_storage.duckdb_variants import DuckDbVariants
from dae.genomic_resources.gene_models import GeneModels
from dae.genomic_resources.reference_genome import ReferenceGenome
from dae.genotype_storage.genotype_storage import GenotypeStorage
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.schema2_storage.schema2_import_storage import Schema2DatasetLayout
from dae.utils import fs_utils

logger = logging.getLogger(__name__)


def _duckdb_global_connect() -> duckdb.DuckDBPyConnection:
    logger.info("connection to inmemory duckdb")
    return duckdb.connect(":memory:")


def _duckdb_db_connect(
    db_filename: str, *,
    read_only: bool = True,
) -> duckdb.DuckDBPyConnection:
    logger.info(
        "duckdb connection to %s; read_only=%s", db_filename, read_only)
    try:
        return duckdb.connect(db_filename, read_only=read_only)
    except duckdb.ConnectionException:
        logger.exception(
            "duckdb connection error: %s; read_only=%s",
            db_filename, read_only)
        raise


def duckdb_connect(
    db_name: str | None = None, *,
    read_only: bool = True,
) -> duckdb.DuckDBPyConnection:
    if db_name is not None:
        return _duckdb_db_connect(db_name, read_only=read_only)
    return _duckdb_global_connect()


PARQUET_SCAN = re.compile(r"parquet_scan\('(?P<parquet_path>.+)'\)")


class DuckDbGenotypeStorage(GenotypeStorage, DuckDbConnectionFactory):
    """Defines DuckDb genotype storage."""

    VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "storage_type": {
            "type": "string",
            "allowed": ["duckdb_legacy", "duckdb2"],
        },
        "id": {
            "type": "string", "required": True,
        },
        "db": {
            "type": "string",
        },
        "read_only": {
            "type": "boolean",
            "default": True,
        },
        "memory_limit": {
            "type": "string",
            "default": "16GB",
        },
        "base_dir": {
            "type": "string",
        },
        "endpoint_url": {
            "type": "string",
        },
        "work_dir": {
            "type": "string",
        },
    }

    def __init__(self, storage_config: dict[str, Any]):
        super().__init__(storage_config)
        self.connection_factory: duckdb.DuckDBPyConnection | None = None

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
        if base_dir and not (
                os.path.isabs(base_dir) or fs_utils.is_s3url(base_dir)):
            raise ValueError(
                f"DuckDb genotype storage base dir should be an "
                f"absolute path or S3 bucket; <{base_dir}> passed instead.")
        return result

    @classmethod
    def get_storage_types(cls) -> set[str]:
        return {"duckdb_legacy", "duckdb2"}

    def _s3_secret_clause(self) -> str:
        endpoint_url = self.storage_config.get("endpoint_url")
        endpoint = None
        if endpoint_url:
            parsed = urlparse(endpoint_url)
            endpoint = parsed.netloc

        return jinja2.Template(textwrap.dedent(
            """
                drop secret if exists {{ storage_id }}_secret;

                create secret {{ storage_id }}_secret (
                    type s3,
                    key_id '{{ aws_access_key_id }}',
                    secret '{{ aws_secret_access_key }}',
                    {%- if endpoint %}
                    endpoint '{{ endpoint }}',
                    {%- endif %}
                    url_style 'path',
                    {%- if region %}
                    region '{{ region }}',
                    {%- else %}
                    region 'None'
                    {%- endif %}
                );
            """,
        )).render(
            storage_id=self.storage_id,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            endpoint=endpoint,
            region=os.getenv("AWS_REGION"),
        )

    def _s3_attach_db_clause(self) -> str:
        return jinja2.Template(textwrap.dedent(
            """
                ATTACH DATABASE '{{ db_name }}' (type duckdb, read_only);
            """,
        )).render(
            db_name=self.get_db_filename(),
        )

    def _s3_filesystem(self) -> S3FileSystem:
        client_kwargs = {}
        endpoint_url = self.storage_config.get("endpoint_url")
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url
        s3filesystem = S3FileSystem(anon=False, client_kwargs=client_kwargs)
        s3filesystem.invalidate_cache()
        return s3filesystem

    def _s3_connect(
        self, *,
        read_only: bool = False,
    ) -> duckdb.DuckDBPyConnection:
        connection = _duckdb_global_connect()

        connection.sql("INSTALL httpfs;")
        connection.sql("LOAD httpfs;")

        s3_secret_clause = self._s3_secret_clause()
        connection.sql(s3_secret_clause)

        try:
            if self.get_db() is not None:
                # attach
                assert read_only
                s3_attach_db_clause = self._s3_attach_db_clause()
                time.sleep(5.0)
                connection.sql(s3_attach_db_clause)

            memory_limit = self.get_memory_limit()
            if memory_limit:
                query = f"SET memory_limit='{memory_limit}'"
                logger.info("memory limit: %s", query)
                connection.sql(query)

        except Exception:
            s3_fs = self._s3_filesystem()
            info = s3_fs.info(self.get_db_filename())
            logger.exception(
                "duckdb s3 connection error: secret: %s; attach: %s; info: %s",
                s3_secret_clause, s3_attach_db_clause, info)
            raise

        return connection

    def _is_s3_storage(self) -> bool:
        base_dir = self.get_base_dir()
        if base_dir is None:
            return False
        return fs_utils.is_s3url(base_dir)

    def connect(self) -> duckdb.DuckDBPyConnection:
        if self.connection_factory is None:
            self.start()
        assert self.connection_factory is not None
        return self.connection_factory

    def start(self) -> DuckDbGenotypeStorage:
        if self.connection_factory:
            logger.warning(
                "starting already started DuckDb genotype storage: <%s>",
                self.storage_id)
            return self
        if self._is_s3_storage():
            self.connection_factory = self._s3_connect(read_only=True)
            return self

        db_name = self.get_db()
        if db_name is not None:
            db_name = self.get_db_filename()
            dirname = os.path.dirname(db_name)
            os.makedirs(dirname, exist_ok=True)
            logger.debug("working with duckdb: %s", db_name)
        self.connection_factory = duckdb_connect(
            db_name=db_name, read_only=self.is_read_only())
        memory_limit = self.get_memory_limit()
        if memory_limit:
            query = f"SET memory_limit='{memory_limit}'"
            logger.info("memory limit: %s", query)
            self.connection_factory.sql(query)
        return self

    def _get_local_db_filename(self) -> str:
        assert self.get_db() is not None
        if not self._is_s3_storage():
            return self.get_db_filename()

        db_name = self.get_db()
        work_dir = self.get_work_dir()
        assert db_name is not None
        assert work_dir is not None

        return os.path.join(work_dir, db_name)

    def create_database_connection(self) -> duckdb.DuckDBPyConnection:
        """Create a read-write connection to the DuckDb database."""
        assert self.get_db() is not None
        db_filename = self._get_local_db_filename()
        dirname = os.path.dirname(db_filename)
        os.makedirs(dirname, exist_ok=True)
        logger.info("creating connection to %s", db_filename)

        try:
            connection = duckdb.connect(db_filename, read_only=False)
        except duckdb.ConnectionException:
            logger.exception(
                "duckdb read-write connection error: %s",
                db_filename)
            raise

        memory_limit = self.get_memory_limit()
        if memory_limit:
            query = f"SET memory_limit='{memory_limit}'"
            logger.info("memory limit: %s", query)
            connection.sql(query)
        return connection

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

    def get_base_dir(self) -> str | None:
        return self.storage_config.get("base_dir")

    def get_work_dir(self) -> str | None:
        return self.storage_config.get("work_dir")

    def get_db(self) -> str | None:
        return self.storage_config.get("db")

    def get_db_filename(self) -> str:
        """Construct database full filename."""
        db = self.get_db()
        if db is None:
            raise ValueError("db configuration should be set")
        if os.path.isabs(db):
            return db
        return self._base_dir_join(db)

    def get_memory_limit(self) -> str:
        return cast(str, self.storage_config.get("memory_limit", "32GB"))

    @staticmethod
    def create_table_layout(study_id: str) -> Schema2DatasetLayout:
        return Schema2DatasetLayout(
            study_id,
            f"{study_id}_pedigree",
            f"{study_id}_summary",
            f"{study_id}_family",
            f"{study_id}_meta")

    def create_parquet_scans_layout_relative(
        self,
        study_id: str,
        partition_descriptor: PartitionDescriptor,
    ) -> Schema2DatasetLayout:
        """Construct DuckDb parquet scans relative to base dir."""
        if self.get_base_dir() is None:
            raise ValueError("base_dir configuration should be set")

        study_dir = study_id
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

    def create_table(
        self,
        connection: duckdb.DuckDBPyConnection,
        parquet_path: str,
        table_name: str,
    ) -> None:
        """Create a table from a parquet file."""
        with connection.cursor() as cursor:
            assert cursor is not None
            query = f"DROP TABLE IF EXISTS {table_name}"
            cursor.sql(query)

            query = f"""
                CREATE TABLE {table_name} AS
                SELECT * FROM parquet_scan('{parquet_path}')
            """  # noqa: S608
            cursor.sql(query)

    def create_table_partitioned(
        self,
        connection: duckdb.DuckDBPyConnection,
        parquet_path: str,
        table_name: str,
        partition: list[tuple[str, str]],
    ) -> None:
        """Create a table from a partitioned parquet dataset."""
        with connection.cursor() as cursor:
            dataset_path = f"{parquet_path}/{ '*/' * len(partition)}*.parquet"
            logger.debug("creating table %s from %s", table_name, dataset_path)
            memory_limit = self.get_memory_limit()
            if memory_limit:
                query = f"SET memory_limit='{memory_limit}'"
                logger.info("memory limit: %s", query)
                cursor.sql(query)

            query = f"DROP TABLE IF EXISTS {table_name}"
            logger.debug("query: %s", query)
            cursor.sql(query)

            query = f"""
                CREATE TABLE {table_name} AS
                SELECT * FROM
                parquet_scan('{dataset_path}', hive_partitioning = 1)
            """
            logger.info("query: %s", query)
            cursor.sql(query)

    def _import_tables(
        self,
        connection: duckdb.DuckDBPyConnection,
        study_id: str,
        layout: Schema2DatasetLayout,
        partition_descriptor: PartitionDescriptor,
    ) -> Schema2DatasetLayout:
        tables_layout = self.create_table_layout(study_id)
        self.create_table(
            connection,
            layout.meta, tables_layout.meta)
        self.create_table(
            connection,
            layout.pedigree, tables_layout.pedigree)
        if layout.summary is None:
            assert layout.family is None
            return Schema2DatasetLayout(
                tables_layout.study,
                tables_layout.pedigree,
                None,
                None,
                tables_layout.meta)

        assert tables_layout.summary is not None
        assert tables_layout.family is not None
        assert layout.summary is not None
        assert layout.family is not None
        self.create_table_partitioned(
            connection,
            layout.summary, tables_layout.summary,
            partition_descriptor.dataset_summary_partition())
        self.create_table_partitioned(
            connection,
            layout.family, tables_layout.family,
            partition_descriptor.dataset_family_partition())
        return tables_layout

    def _import_into_database(
        self,
        study_id: str,
        layout: Schema2DatasetLayout,
        partition_descriptor: PartitionDescriptor,
    ) -> Schema2DatasetLayout:
        if self.is_read_only():
            with closing(self.create_database_connection()) as connection:
                tables_layout = self._import_tables(
                    connection, study_id, layout, partition_descriptor)
            if not self._is_s3_storage():
                return tables_layout

            local_db_filename = self._get_local_db_filename()
            s3_db_filename = self.get_db_filename()

            assert local_db_filename != s3_db_filename
            s3_fs = self._s3_filesystem()
            s3_fs.put(local_db_filename, s3_db_filename)

            return tables_layout

        if self.connection_factory is None:
            self.start()
        assert self.connection_factory is not None
        return self._import_tables(
            self.connection_factory, study_id, layout, partition_descriptor)

    def import_dataset(
        self,
        work_dir: str,  # noqa: ARG002
        study_id: str,
        layout: Schema2DatasetLayout,
        partition_descriptor: PartitionDescriptor,
    ) -> Schema2DatasetLayout:
        """Import study parquet dataset into duckdb genotype storage."""
        if self.get_db() is not None:
            return self._import_into_database(
                study_id, layout, partition_descriptor)

        if self.get_base_dir() is not None:
            dest_layout = self.create_parquet_scans_layout_relative(
                study_id, partition_descriptor)

            fs_utils.copy(dest_layout.study, layout.study)
            return dest_layout

        return self.create_parquet_scans_layout_from_layout(
            layout, partition_descriptor)

    def _base_dir_join(self, dir_name: str) -> str:
        base_dir = self.get_base_dir()
        assert base_dir is not None
        return fs_utils.join(base_dir, dir_name)

    def _base_dir_join_parquet_scan_or_table(
            self, parquet_scan: str | None) -> str | None:
        if parquet_scan is None:
            return None
        if self.get_base_dir() is None:
            return parquet_scan

        match = PARQUET_SCAN.fullmatch(parquet_scan)
        if not match:
            return parquet_scan

        parquet_path = match.groupdict()["parquet_path"]
        assert parquet_path
        base_dir = self.get_base_dir()
        assert base_dir is not None

        full_path = fs_utils.join(base_dir, parquet_path)
        return f"parquet_scan('{full_path}')"

    def _strip_db_name(self, db_name: str) -> str:
        return pathlib.Path(db_name).stem

    def build_backend(
            self, study_config: dict,
            genome: ReferenceGenome,
            gene_models: GeneModels) -> DuckDbVariants | DuckDb2Variants:
        if self.connection_factory is None:
            self.start()

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
            db_name = self._strip_db_name(db_name)

        if self.connection_factory is None:
            raise ValueError(
                f"duckdb genotype storage not started: "
                f"{self.storage_config}")
        assert self.connection_factory is not None

        if self.storage_type == "duckdb_legacy":
            return DuckDbVariants(
                self,
                db_name,
                tables_layout.family,
                tables_layout.summary,
                tables_layout.pedigree,
                tables_layout.meta,
                gene_models)

        if self.storage_type == "duckdb2":
            db_layout = Db2Layout(
                db=db_name,
                study=study_config["id"],
                pedigree=tables_layout.pedigree,
                summary=tables_layout.summary,
                family=tables_layout.family,
                meta=tables_layout.meta,
            )

            assert db_layout is not None
            return DuckDb2Variants(
                self,
                db_layout,
                gene_models,
                genome,
            )

        raise ValueError(
            f"Unsuported DuckDb storage type: {self.storage_type}")


class AbstractDuckDbStorage(GenotypeStorage, DuckDbConnectionFactory):
    """Defines abstract DuckDb genotype storage."""

    def __init__(
        self,
        dd_config: DuckDbConf | DuckDbParquetConf | DuckDbS3ParquetConf,
    ):
        super().__init__(dd_config.model_dump())
        self.dd_config = dd_config
        self.connection_factory: duckdb.DuckDBPyConnection | None = None

    def _memory_limit_clause(self) -> str | None:
        memory_limit = self.dd_config.memory_limit
        if memory_limit is None:
            return None

        mlimit = memory_limit.human_readable(decimal=True)
        return f"SET memory_limit='{mlimit}'"

    def shutdown(self) -> AbstractDuckDbStorage:
        if self.connection_factory is None:
            logger.warning(
                "trying to shutdown already stopped DuckDbGenotypeStorage")
            return self
        self.connection_factory.close()
        self.connection_factory = None
        return self

    def connect(self) -> duckdb.DuckDBPyConnection:
        if self.connection_factory is None:
            self.start()
        assert self.connection_factory is not None
        return self.connection_factory

    def get_study_config_tables(
        self,
        study_config: dict[str, Any],
    ) -> Db2Layout:
        """Return the study tables configuration."""
        tables = study_config["genotype_storage"]["tables"]
        db_name = None
        if self.storage_type in {"duckdb", "duckdb_s3", "duckdb_legacy"}:
            db_name = self.storage_config.get("db")
        return Db2Layout(
            db=db_name,
            study=study_config["id"],
            pedigree=tables["pedigree"],
            summary=tables.get("summary"),
            family=tables.get("family"),
            meta=tables["meta"],
        )

    @abc.abstractmethod
    def import_dataset(
        self,
        work_dir: str,
        study_id: str,
        layout: Schema2DatasetLayout,
        partition_descriptor: PartitionDescriptor,
    ) -> Schema2DatasetLayout:
        """Import study parquet dataset into a DuckDb genotype storage."""

    @abc.abstractmethod
    def build_study_layout(
        self,
        study_config: dict[str, Any],
    ) -> Db2Layout:
        """Construct study layout from study and storage configuration."""

    def build_backend(
            self, study_config: dict,
            genome: ReferenceGenome,
            gene_models: GeneModels) -> DuckDbVariants | DuckDb2Variants:
        if self.connection_factory is None:
            self.start()

        tables_layout = self.build_study_layout(study_config)

        if self.connection_factory is None:
            raise ValueError(
                f"duckdb genotype storage not started: "
                f"{self.storage_config}")
        assert self.connection_factory is not None

        if self.storage_type == "duckdb_legacy":
            return DuckDbVariants(
                self,
                tables_layout.db,
                tables_layout.family,
                tables_layout.summary,
                tables_layout.pedigree,
                tables_layout.meta,
                gene_models)

        return DuckDb2Variants(
            self,
            tables_layout,
            gene_models,
            genome,
        )


def _join_base_url_and_parquet_scan(
    base_url: str,
    parquet_scan: str | None,
) -> str | None:
    if parquet_scan is None:
        return None

    match = PARQUET_SCAN.fullmatch(parquet_scan)
    if not match:
        return parquet_scan

    parquet_path = match.groupdict()["parquet_path"]
    assert parquet_path
    assert base_url is not None

    full_path = fs_utils.join(base_url, parquet_path)
    return f"parquet_scan('{full_path}')"


def _create_relative_parquet_scans_layout(
    base_url: str,
    study_id: str,
    partition_descriptor: PartitionDescriptor,
) -> Schema2DatasetLayout:
    """Construct DuckDb parquet scans relative to base dir."""

    study_dir = study_id
    pedigree_path = fs_utils.join(study_dir, "pedigree")
    meta_path = fs_utils.join(study_dir, "meta")
    summary_path = fs_utils.join(study_dir, "summary")
    summary_partition = partition_descriptor.dataset_summary_partition()
    family_path = fs_utils.join(study_dir, "family")
    family_partition = partition_descriptor.dataset_family_partition()
    study_dir = fs_utils.join(base_url, study_dir)
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
        self.connection_factory = duckdb.connect(":memory:")

        memory_limit = self._memory_limit_clause()
        if memory_limit:
            logger.info("memory limit: %s", memory_limit)
            self.connection_factory.sql(memory_limit)

        return self

    @classmethod
    def get_storage_types(cls) -> set[str]:
        return {"duckdb_parquet"}

    def build_study_layout(
        self,
        study_config: dict[str, Any],
    ) -> Db2Layout:
        study_config_layout = self.get_study_config_tables(study_config)
        assert study_config_layout.db is None
        base_url = str(self.config.base_dir)

        pedigree = _join_base_url_and_parquet_scan(
            base_url, study_config_layout.pedigree)
        meta = _join_base_url_and_parquet_scan(
            base_url, study_config_layout.meta)
        assert pedigree is not None
        assert meta is not None

        return Db2Layout(
            db=None,
            study=study_config_layout.study,
            pedigree=pedigree,
            summary=_join_base_url_and_parquet_scan(
                base_url, study_config_layout.summary),
            family=_join_base_url_and_parquet_scan(
                base_url, study_config_layout.family),
            meta=meta,
        )

    def import_dataset(
        self,
        work_dir: str,  # noqa: ARG002
        study_id: str,
        layout: Schema2DatasetLayout,
        partition_descriptor: PartitionDescriptor,
    ) -> Schema2DatasetLayout:
        """Import study parquet dataset into duckdb genotype storage."""

        dest_layout = _create_relative_parquet_scans_layout(
            str(self.config.base_dir),
            study_id,
            partition_descriptor,
        )

        fs_utils.copy(dest_layout.study, layout.study)
        return dest_layout


def duckdb_parquet_storage_factory(
    storage_config: dict[str, Any],
) -> DuckDbParquetStorage:
    """Create `duckdb_parquet` genotype storage."""
    dd_config = parse_duckdb_config(storage_config)
    if dd_config.storage_type != "duckdb_parquet":
        raise TypeError(
            f"unexpected storage type: {dd_config.storage_type}")
    return DuckDbParquetStorage(dd_config)


def _s3_secret_clause(
    storage_id: str,
    endpoint_url: str | S3Path | None,
) -> str:
    endpoint = None
    if endpoint_url:
        parsed = urlparse(str(endpoint_url))
        endpoint = parsed.netloc

    return jinja2.Template(textwrap.dedent(
        """
            drop secret if exists {{ storage_id }}_secret;

            create secret {{ storage_id }}_secret (
                type s3,
                key_id '{{ aws_access_key_id }}',
                secret '{{ aws_secret_access_key }}',
                {%- if endpoint %}
                endpoint '{{ endpoint }}',
                {%- endif %}
                url_style 'path',
                {%- if region %}
                region '{{ region }}',
                {%- else %}
                region 'None'
                {%- endif %}
            );
        """,
    )).render(
        storage_id=storage_id,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        endpoint=endpoint,
        region=os.getenv("AWS_REGION"),
    )


def _s3_attach_db_clause(db_url: str) -> str:
    return f"ATTACH DATABASE '{ db_url }' (type duckdb, read_only);"


def _s3_filesystem(endpoint_url: str | S3Path | None) -> S3FileSystem:
    client_kwargs = {}
    if endpoint_url:
        client_kwargs["endpoint_url"] = str(endpoint_url)
    s3filesystem = S3FileSystem(anon=False, client_kwargs=client_kwargs)
    s3filesystem.invalidate_cache()
    return s3filesystem


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
        self.connection_factory = duckdb.connect(":memory:")

        memory_limit = self._memory_limit_clause()
        if memory_limit:
            logger.info("memory limit: %s", memory_limit)
            self.connection_factory.sql(memory_limit)

        s3_secret_clause = _s3_secret_clause(
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
        study_config_layout = self.get_study_config_tables(study_config)
        assert study_config_layout.db is None
        base_url = str(self.config.bucket_url)

        pedigree = _join_base_url_and_parquet_scan(
            base_url, study_config_layout.pedigree)
        meta = _join_base_url_and_parquet_scan(
            base_url, study_config_layout.meta)
        assert pedigree is not None
        assert meta is not None

        return Db2Layout(
            db=None,
            study=study_config_layout.study,
            pedigree=pedigree,
            summary=_join_base_url_and_parquet_scan(
                base_url, study_config_layout.summary),
            family=_join_base_url_and_parquet_scan(
                base_url, study_config_layout.family),
            meta=meta,
        )

    def import_dataset(
        self,
        work_dir: str,  # noqa: ARG002
        study_id: str,
        layout: Schema2DatasetLayout,
        partition_descriptor: PartitionDescriptor,
    ) -> Schema2DatasetLayout:
        """Import study parquet dataset into duckdb genotype storage."""

        dest_layout = _create_relative_parquet_scans_layout(
            str(self.config.bucket_url),
            study_id,
            partition_descriptor,
        )

        s3_fs = _s3_filesystem(self.config.endpoint_url)
        s3_fs.put(layout.study, dest_layout.study, recursive=True)

        return dest_layout


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

    def is_read_only(self) -> bool:
        return self.config.read_only

    def start(self) -> DuckDbStorage:
        if self.connection_factory:
            logger.warning(
                "starting already started DuckDb genotype storage: <%s>",
                self.storage_id)
            return self
        db_filename = self.get_db_filename()
        self.connection_factory = self.create_database_connection(
            db_filename,
            read_only=self.is_read_only())
        memory_limit_clause = self._memory_limit_clause()
        if memory_limit_clause:
            self.connection_factory.sql(memory_limit_clause)
        return self

    @staticmethod
    def create_database_connection(
        db_filename: str, *,
        read_only: bool = True,
    ) -> duckdb.DuckDBPyConnection:
        """Create a read-write connection to the DuckDb database."""
        dirname = os.path.dirname(db_filename)
        os.makedirs(dirname, exist_ok=True)
        logger.debug("working with duckdb: %s", db_filename)
        return duckdb_connect(
            db_name=db_filename, read_only=read_only)

    def get_db_filename(self) -> str:
        """Construct database full filename."""
        db = self.config.db
        if db.is_absolute():
            return str(db)
        return str(self.config.base_dir / db)

    @staticmethod
    def create_table_layout(study_id: str) -> Schema2DatasetLayout:
        return Schema2DatasetLayout(
            study_id,
            f"{study_id}_pedigree",
            f"{study_id}_summary",
            f"{study_id}_family",
            f"{study_id}_meta")

    def create_table(
        self,
        connection: duckdb.DuckDBPyConnection,
        parquet_path: str,
        table_name: str,
    ) -> None:
        """Create a table from a parquet file."""
        with connection.cursor() as cursor:
            assert cursor is not None
            query = f"DROP TABLE IF EXISTS {table_name}"
            cursor.sql(query)

            query = f"""
                CREATE TABLE {table_name} AS
                SELECT * FROM parquet_scan('{parquet_path}')
            """  # noqa: S608
            cursor.sql(query)

    def create_table_partitioned(
        self,
        connection: duckdb.DuckDBPyConnection,
        parquet_path: str,
        table_name: str,
        partition: list[tuple[str, str]],
    ) -> None:
        """Create a table from a partitioned parquet dataset."""
        with connection.cursor() as cursor:
            dataset_path = f"{parquet_path}/{ '*/' * len(partition)}*.parquet"
            logger.debug("creating table %s from %s", table_name, dataset_path)
            memory_limit = self._memory_limit_clause()
            if memory_limit:
                logger.info("memory limit: %s", memory_limit)
                cursor.sql(memory_limit)

            query = f"DROP TABLE IF EXISTS {table_name}"
            logger.debug("query: %s", query)
            cursor.sql(query)

            query = f"""
                CREATE TABLE {table_name} AS
                SELECT * FROM
                parquet_scan('{dataset_path}', hive_partitioning = 1)
            """
            logger.info("query: %s", query)
            cursor.sql(query)

    def _create_tables(
        self,
        connection: duckdb.DuckDBPyConnection,
        study_id: str,
        layout: Schema2DatasetLayout,
        partition_descriptor: PartitionDescriptor,
    ) -> Schema2DatasetLayout:
        tables_layout = self.create_table_layout(study_id)
        self.create_table(
            connection,
            layout.meta, tables_layout.meta)
        self.create_table(
            connection,
            layout.pedigree, tables_layout.pedigree)
        if layout.summary is None:
            assert layout.family is None
            return Schema2DatasetLayout(
                tables_layout.study,
                tables_layout.pedigree,
                None,
                None,
                tables_layout.meta)

        assert tables_layout.summary is not None
        assert tables_layout.family is not None
        assert layout.summary is not None
        assert layout.family is not None
        self.create_table_partitioned(
            connection,
            layout.summary, tables_layout.summary,
            partition_descriptor.dataset_summary_partition())
        self.create_table_partitioned(
            connection,
            layout.family, tables_layout.family,
            partition_descriptor.dataset_family_partition())
        return tables_layout

    def import_dataset(
        self,
        work_dir: str,
        study_id: str,
        layout: Schema2DatasetLayout,
        partition_descriptor: PartitionDescriptor,
    ) -> Schema2DatasetLayout:
        """Import study parquet dataset into duckdb genotype storage."""
        work_db_filename = os.path.join(work_dir, self.config.db)
        with closing(self.create_database_connection(
                work_db_filename, read_only=False),
            ) as connection:
            work_tables = self._create_tables(
                connection,
                study_id,
                layout,
                partition_descriptor,
            )

        # reconnect the storage
        if self.connection_factory is not None:
            self.shutdown()

        db_filename = self.get_db_filename()
        if not os.path.exists(db_filename):
            logger.warning(
                "replacing existing DuckDb database: %s",
                db_filename)

        assert self.connection_factory is None
        fs_utils.copy(db_filename, work_db_filename)

        return work_tables

    def build_study_layout(
        self,
        study_config: dict[str, Any],
    ) -> Db2Layout:
        study_config_layout = self.get_study_config_tables(study_config)
        db_name = pathlib.Path(self.get_db_filename()).stem
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
    """Create `duckdb_s3_parquet` genotype storage."""
    dd_config = parse_duckdb_config(storage_config)
    if dd_config.storage_type != "duckdb":
        raise TypeError(
            f"unexpected storage type: {dd_config.storage_type}")
    return DuckDbStorage(dd_config)
