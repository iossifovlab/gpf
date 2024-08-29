# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from pydantic import ValidationError

from dae.duckdb_storage.duckdb_storage_config import (
    DuckDbConf,
    DuckDbParquetConf,
    DuckDbS3Conf,
    parse_duckdb_config,
)


def test_duckdb_config() -> None:
    config = {
        "storage_type": "duckdb",
        "id": "id",
        "db": "db",
        "base_dir": "/storage/base_dir",
    }
    dd_config = parse_duckdb_config(config)
    assert dd_config
    assert isinstance(dd_config, DuckDbConf)


def test_duckdb_config_abs_base_dir() -> None:
    config = {
        "storage_type": "duckdb",
        "id": "id",
        "db": "db",
        "base_dir": "storage/base_dir",
    }
    with pytest.raises(
            ValueError,
            match="base dir <storage/base_dir> must be absolute path"):
        parse_duckdb_config(config)


def test_duckdb_config_missing_params() -> None:
    with pytest.raises(
            ValidationError,
            match="1 validation error for DuckDbConf\ndb"):
        parse_duckdb_config({
            "storage_type": "duckdb",
            "id": "id",
            "base_dir": "/storage/base_dir",
        })

    with pytest.raises(
            ValidationError,
            match="1 validation error for DuckDbConf\nid"):
        parse_duckdb_config({
            "storage_type": "duckdb",
            "db": "db.duckdb",
            "base_dir": "/storage/base_dir",
        })

    with pytest.raises(
            ValidationError,
            match="1 validation error for DuckDbConf\nbase_dir"):
        parse_duckdb_config({
            "storage_type": "duckdb",
            "id": "id",
            "db": "db.duckdb",
        })


def test_duckdb_parquet_config() -> None:
    config = {
        "storage_type": "duckdb-parquet",
        "id": "id",
        "base_dir": "/storage/base_dir",
    }
    dd_config = parse_duckdb_config(config)
    assert dd_config
    assert isinstance(dd_config, DuckDbParquetConf)


def test_duckdb_parquet_config_missing_params() -> None:
    with pytest.raises(
            ValidationError,
            match="1 validation error for DuckDbParquetConf\nid"):
        parse_duckdb_config({
            "storage_type": "duckdb-parquet",
            "base_dir": "/storage/base_dir",
        })

    with pytest.raises(
            ValidationError,
            match="1 validation error for DuckDbParquetConf\nbase_dir"):
        parse_duckdb_config({
            "storage_type": "duckdb-parquet",
            "id": "id",
        })


def test_duckdb_s3_config() -> None:
    dd_config = parse_duckdb_config({
        "storage_type": "duckdb-s3",
        "id": "id",
        "db": "db",
        "bucket_url": "s3://duckdb/storage/studies",
    })
    assert dd_config
    assert isinstance(dd_config, DuckDbS3Conf)

    dd_config = parse_duckdb_config({
        "storage_type": "duckdb-s3",
        "id": "id",
        "db": "db",
        "bucket_url": "s3://duckdb/storage/studies",
        "endpoint_url": "http://localhost:9000",
    })
    assert dd_config
    assert isinstance(dd_config, DuckDbS3Conf)

    dd_config = parse_duckdb_config({
        "storage_type": "duckdb-s3",
        "id": "id",
        "db": "db",
        "bucket_url": "s3://duckdb/storage/studies",
        "endpoint_url": "http://localhost:9000",
        "work_dir": "/storage/work_dir",
    })
    assert dd_config
    assert isinstance(dd_config, DuckDbS3Conf)


def test_duckdb_s3_config_bad_urls() -> None:
    with pytest.raises(
            ValidationError,
            match="1 validation error for DuckDbS3Conf\nbucket_url"):
        parse_duckdb_config({
            "storage_type": "duckdb-s3",
            "id": "id",
            "db": "db",
            "bucket_url": "https://duckdb/storage/studies",
            "endpoint_url": "https://localhost:9000",
        })

    with pytest.raises(
            ValidationError,
            match="1 validation error for DuckDbS3Conf\nendpoint_url"):
        parse_duckdb_config({
            "storage_type": "duckdb-s3",
            "id": "id",
            "db": "db",
            "bucket_url": "s3://duckdb/storage/studies",
            "endpoint_url": "ftp://localhost:9000",
        })
