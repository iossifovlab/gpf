from __future__ import annotations

import logging
import pathlib
from typing import Literal

import duckdb
from deprecation import deprecated
from fsspec.core import url_to_fs

from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.utils import fs_utils

logger = logging.getLogger(__name__)


def _collect_input_parquet_files(
    parquets_dir: str,
    variants_type: Literal["summary", "family"] | None = None,
) -> list[str]:
    if variants_type is not None:
        parquet_pattern = f"**/{variants_type}_*.parquet"
    else:
        parquet_pattern = "**/*.parquet"

    parquet_files = fs_utils.glob(
        fs_utils.join(parquets_dir, parquet_pattern),
    )
    return sorted(parquet_files)


def _filter_output_parquet_file(
    parquet_files: list[str],
    output_parquet_filename: str,
) -> list[str]:
    """Filter out the output parquet file from the list of input files."""
    return [
        fn for fn in parquet_files
        if not fn.endswith(output_parquet_filename)
    ]


def merge_parquets(
    in_files: list[str], out_file: str,
    *,
    delete_in_files: bool = True,
    row_group_size: int = 50_000,
) -> None:
    """Merge multiple parquet files into a single parquet file."""
    if len(in_files) == 0:
        raise OSError("no input files provided for merging")
    assert len(in_files) > 0

    try:
        with duckdb.connect() as con:
            con.execute("SET memory_limit = '768MB';")
            con.execute("SET threads = 1;")
            con.execute(f"SET temp_directory = '{out_file}.tmp';")
            con.from_parquet(in_files).to_parquet(
                out_file,
                row_group_size=row_group_size,
                overwrite=True,
                compression="zstd",
            )
    except duckdb.InvalidInputException as err:
        logger.exception(
            "invalid input parquet file(s) in: %s", in_files)
        raise OSError(
            f"invalid input parquet file(s) in: {in_files}",
        ) from err

    if delete_in_files:
        for in_file in in_files:
            try:
                fs, path = url_to_fs(in_file)
                fs.rm_file(path)
            except FileNotFoundError:
                logger.warning("missing chunk parquet file: %s", in_file)


def merge_parquet_directory(
    parquets_dir: pathlib.Path | str,
    output_parquet_filename: str, *,
    variants_type: Literal["summary", "family"] | None = None,
    row_group_size: int = 50_000,
    delete_in_files: bool = True,
) -> None:
    """Merge all parquet files from parquets_dir into a single parquet file."""
    if isinstance(parquets_dir, pathlib.Path):
        parquets_dir = str(parquets_dir)

    parquet_files = _collect_input_parquet_files(
        parquets_dir, variants_type=variants_type,
    )

    parquet_files = _filter_output_parquet_file(
        parquet_files, output_parquet_filename,
    )

    if len(parquet_files) > 0:
        logger.debug(
            "Merging %d files in %s", len(parquet_files), parquets_dir,
        )
        merge_parquets(
            parquet_files, output_parquet_filename,
            row_group_size=row_group_size,
            delete_in_files=delete_in_files)


@deprecated(
    "dae.parquet.schema2.merge_variants_parquet is deprecated. "
    "Use dae.parquet.schema2.merge_parquet_directory instead.",
)
def merge_variants_parquets(
    partition_descriptor: PartitionDescriptor,
    variants_dir: str,
    partition: list[tuple[str, str]],
    row_group_size: int = 50_000,
    variants_type: Literal["summary", "family"] | None = None,
) -> None:
    """Merge parquet files in variants_dir."""
    output_parquet_file = fs_utils.join(
        variants_dir,
        partition_descriptor.partition_filename(
            "merged", partition, bucket_index=None,
        ),
    )
    if variants_type is not None:
        parquet_glob = f"{variants_type}_*.parquet"
    else:
        parquet_glob = "*.parquet"
    parquet_files = sorted(fs_utils.glob(
        fs_utils.join(variants_dir, parquet_glob),
    ))

    is_output_in_input = \
        any(fn.endswith(output_parquet_file) for fn in parquet_files)
    if is_output_in_input:
        # a leftover file from a previous run. Remove from list of files.
        # we use endswith instead of == because of path normalization
        for i, filename in enumerate(parquet_files):
            if filename.endswith(output_parquet_file):
                parquet_files.pop(i)
                break

    if len(parquet_files) > 0:
        logger.info(
            "Merging %d files in %s", len(parquet_files), variants_dir,
        )
        merge_parquets(
            parquet_files, output_parquet_file,
            row_group_size=row_group_size)
