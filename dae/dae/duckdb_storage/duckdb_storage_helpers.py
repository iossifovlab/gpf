from __future__ import annotations

import logging
import os
import re
import textwrap
from typing import Any
from urllib.parse import urlparse

import duckdb
import jinja2
from pydantic import (
    ByteSize,
)
from s3fs.core import S3FileSystem

from dae.duckdb_storage.duckdb2_variants import (
    Db2Layout,
)
from dae.duckdb_storage.duckdb_storage_config import (
    S3Path,
)
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.schema2_storage.schema2_import_storage import Schema2DatasetLayout
from dae.utils import fs_utils

logger = logging.getLogger(__name__)
PARQUET_SCAN = re.compile(r"parquet_scan\('(?P<parquet_path>.+)'\)")


def create_database_connection(
    db_filename: str, *,
    read_only: bool = True,
    memory_limit: str | ByteSize | None = None,
) -> duckdb.DuckDBPyConnection:
    """Create a read-write connection to the DuckDb database."""
    dirname = os.path.dirname(db_filename)
    os.makedirs(dirname, exist_ok=True)
    logger.debug("working with duckdb: %s", db_filename)
    logger.info(
        "duckdb connection to %s; read_only=%s", db_filename, read_only)
    try:
        connection = duckdb.connect(db_filename, read_only=read_only)
        if memory_limit is not None:
            if isinstance(memory_limit, ByteSize):
                mlimit = memory_limit.human_readable(decimal=True)
            else:
                mlimit = memory_limit
            connection.sql(f"SET memory_limit='{mlimit}'")
    except duckdb.ConnectionException:
        logger.exception(
            "duckdb connection error: %s; read_only=%s",
            db_filename, read_only)
        raise

    return connection


def create_memory_connection(
    *,
    memory_limit: str | ByteSize | None = None,
) -> duckdb.DuckDBPyConnection:
    """Create a read-write connection to the DuckDb database."""
    try:
        connection = duckdb.connect(":memory:")
        if memory_limit is not None:
            if isinstance(memory_limit, ByteSize):
                mlimit = memory_limit.human_readable(decimal=True)
            else:
                mlimit = memory_limit
            connection.sql(f"SET memory_limit='{mlimit}'")
    except duckdb.ConnectionException:
        logger.exception(
            "duckdb connection ':memory:' error")
        raise

    return connection


def create_table_layout(study_id: str) -> Schema2DatasetLayout:
    return Schema2DatasetLayout(
        study_id,
        f"{study_id}_pedigree",
        f"{study_id}_summary",
        f"{study_id}_family",
        f"{study_id}_meta")


def _create_table(
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


def _create_table_partitioned(
    connection: duckdb.DuckDBPyConnection,
    parquet_path: str,
    table_name: str,
    partition: list[tuple[str, str]],
) -> None:
    """Create a table from a partitioned parquet dataset."""
    with connection.cursor() as cursor:
        dataset_path = f"{parquet_path}/{'*/' * len(partition)}*.parquet"
        logger.debug("creating table %s from %s", table_name, dataset_path)

        query = f"DROP TABLE IF EXISTS {table_name}"
        logger.debug("query: %s", query)
        cursor.sql(query)

        query = f"""
            CREATE TABLE {table_name} AS
            SELECT * FROM
            parquet_scan('{dataset_path}', hive_partitioning = 1)
        """  # noqa: S608
        logger.info("query: %s", query)
        cursor.sql(query)


def create_duckdb_tables(
    connection: duckdb.DuckDBPyConnection,
    study_id: str,
    layout: Schema2DatasetLayout,
    partition_descriptor: PartitionDescriptor,
) -> Schema2DatasetLayout:
    """Create tables in the DuckDb database."""
    tables_layout = create_table_layout(study_id)
    _create_table(
        connection,
        layout.meta, tables_layout.meta)
    _create_table(
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
    _create_table_partitioned(
        connection,
        layout.summary, tables_layout.summary,
        partition_descriptor.summary_partition_schema())
    _create_table_partitioned(
        connection,
        layout.family, tables_layout.family,
        partition_descriptor.family_partition_schema())
    return tables_layout


def join_base_url_and_parquet_scan(
    base_url: str,
    parquet_scan: str | None,
) -> str | None:
    """Join the base URL and the parquet scan."""
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


def create_study_parquet_tables_layout(
    study_config: dict[str, Any],
    base_url: str,
) -> Db2Layout:
    """Construct study tables layout."""
    study_config_layout = get_study_config_tables(
        study_config, db_name=None)
    assert study_config_layout.db is None

    pedigree = join_base_url_and_parquet_scan(
        base_url, study_config_layout.pedigree)
    meta = join_base_url_and_parquet_scan(
        base_url, study_config_layout.meta)
    assert pedigree is not None
    assert meta is not None

    return Db2Layout(
        db=None,
        study=study_config_layout.study,
        pedigree=pedigree,
        summary=join_base_url_and_parquet_scan(
            base_url, study_config_layout.summary),
        family=join_base_url_and_parquet_scan(
            base_url, study_config_layout.family),
        meta=meta,
    )


def create_relative_parquet_scans_layout(
    base_url: str,
    study_id: str,
    partition_descriptor: PartitionDescriptor,
) -> Schema2DatasetLayout:
    """Construct DuckDb parquet scans relative to base dir."""

    study_dir = study_id
    pedigree_path = fs_utils.join(study_dir, "pedigree")
    meta_path = fs_utils.join(study_dir, "meta")
    summary_path = fs_utils.join(study_dir, "summary")
    summary_partition = partition_descriptor.summary_partition_schema()
    family_path = fs_utils.join(study_dir, "family")
    family_partition = partition_descriptor.family_partition_schema()
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


def get_study_config_tables(
    study_config: dict[str, Any],
    db_name: str | None,
) -> Db2Layout:
    """Return the study tables configuration."""
    tables = study_config["genotype_storage"]["tables"]
    return Db2Layout(
        db=db_name,
        study=study_config["id"],
        pedigree=tables["pedigree"],
        summary=tables.get("summary"),
        family=tables.get("family"),
        meta=tables["meta"],
    )


def create_s3_secret_clause(
    storage_id: str,
    endpoint_url: str | S3Path | None,
) -> str:
    """Create a DuckDb secret clause for S3 storage."""
    endpoint = None
    if endpoint_url:
        parsed = urlparse(str(endpoint_url))
        endpoint = parsed.netloc or parsed.path

    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region = os.getenv("AWS_REGION")
    if aws_region is None:
        aws_region = "us-east-1"

    return jinja2.Template(textwrap.dedent(
        """
            create secret (
                type s3,
                key_id '{{ aws_access_key_id }}',
                secret '{{ aws_secret_access_key }}',
                {%- if endpoint %}
                endpoint '{{ endpoint }}',
                {%- if 'amazonaws.com' not in endpoint %}
                url_style 'path',
                {%- endif %}
                {%- endif %}
                {%- if aws_region %}
                region '{{ aws_region }}'
                {%- else %}
                region 'None'
                {%- endif %}
            );
        """,
    )).render(
        storage_id=storage_id,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_region=aws_region,
        endpoint=endpoint,
    )


def create_s3_attach_db_clause(db_url: str) -> str:
    return f"ATTACH DATABASE '{db_url}' (type duckdb, read_only);"


def create_s3_filesystem(endpoint_url: str | S3Path | None) -> S3FileSystem:
    client_kwargs = {}
    if endpoint_url:
        client_kwargs["endpoint_url"] = str(endpoint_url)
    s3filesystem = S3FileSystem(anon=False, client_kwargs=client_kwargs)
    s3filesystem.invalidate_cache()
    return s3filesystem
