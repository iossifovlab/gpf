from __future__ import annotations

import pathlib
from typing import Annotated, Any, Literal

from pydantic import (
    AnyUrl,
    BaseModel,
    ConfigDict,
    HttpUrl,
    UrlConstraints,
)
from pydantic.functional_validators import AfterValidator


def _validate_abs_path(path: pathlib.Path) -> pathlib.Path:
    if not path.is_absolute():
        raise ValueError(f"base dir <{path}> must be absolute path")
    return path


BaseDirPath = Annotated[
    pathlib.Path,
    AfterValidator(_validate_abs_path),
]

S3Path = Annotated[
    AnyUrl,  # type: ignore
    UrlConstraints(allowed_schemes=["s3"]),
]


class DuckDbConf(BaseModel):
    """`duckdb` storage configuration class."""
    model_config = ConfigDict(extra="forbid")

    storage_type: Literal["duckdb"]
    id: str
    db: pathlib.Path
    read_only: bool = True
    base_dir: BaseDirPath


class DuckDbParquetConf(BaseModel):
    """`duckdb-parquet` storage configuration class."""
    model_config = ConfigDict(extra="forbid")

    storage_type: Literal["duckdb-parquet"]
    id: str
    base_dir: BaseDirPath


class DuckDbS3Conf(BaseModel):
    """`duckdb-s3` storage configuration class."""
    model_config = ConfigDict(extra="forbid")

    storage_type: Literal["duckdb-s3"]
    id: str
    db: str
    bucket_url: S3Path
    endpoint_url: HttpUrl | None = None
    work_dir: pathlib.Path | None = None


class DuckDbS3ParquetConf(BaseModel):
    """`duckdb-parquet` storage configuration class."""
    model_config = ConfigDict(extra="forbid")

    storage_type: Literal["duckdb-s3-parquet"]
    id: str
    bucket_url: S3Path
    endpoint_url: HttpUrl | None = None


def parse_duckdb_config(
    config: dict[str, Any],
) -> DuckDbConf | DuckDbParquetConf | DuckDbS3Conf | DuckDbS3ParquetConf:
    """Parse `duckdb` storage configuration."""
    storage_type = config.get("storage_type")
    if storage_type == "duckdb":
        return DuckDbConf(**config)
    if storage_type == "duckdb-parquet":
        return DuckDbParquetConf(**config)
    if storage_type == "duckdb-s3":
        return DuckDbS3Conf(**config)
    if storage_type == "duckdb-s3-parquet":
        return DuckDbS3ParquetConf(**config)
    raise ValueError(f"unexpected storage type: {storage_type}")
