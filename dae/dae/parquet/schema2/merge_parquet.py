from __future__ import annotations

import logging
import pathlib

from dae.parquet.helpers import merge_parquets
from dae.utils import fs_utils

logger = logging.getLogger(__name__)


def _collect_input_parquet_files(
    parquets_dir: str,
) -> list[str]:
    parquet_files = fs_utils.glob(
        fs_utils.join(parquets_dir, "*.parquet"),
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


def merge_parquet_directory(
    parquets_dir: pathlib.Path | str,
    output_parquet_filename: str,
    row_group_size: int = 50_000,
    parquet_version: str | None = None,
) -> None:
    """Merge all parquet files from parquets_dir into a single parquet file."""
    if isinstance(parquets_dir, pathlib.Path):
        parquets_dir = str(parquets_dir)

    parquet_files = _collect_input_parquet_files(parquets_dir)

    parquet_files = _filter_output_parquet_file(
        parquet_files, output_parquet_filename,
    )

    if len(parquet_files) > 0:
        logger.info(
            "Merging %d files in %s", len(parquet_files), parquets_dir,
        )
        merge_parquets(
            parquet_files, output_parquet_filename,
            row_group_size=row_group_size,
            parquet_version=parquet_version)
