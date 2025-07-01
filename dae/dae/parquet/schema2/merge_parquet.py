from __future__ import annotations

import logging

from dae.parquet.helpers import merge_parquets
from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.utils import fs_utils

logger = logging.getLogger(__name__)


def merge_variants_parquets(
    partition_descriptor: PartitionDescriptor,
    variants_dir: str,
    partition: list[tuple[str, str]],
    row_group_size: int = 50_000,
    parquet_version: str | None = None,
) -> None:
    """Merge parquet files in variants_dir."""
    output_parquet_file = fs_utils.join(
        variants_dir,
        partition_descriptor.partition_filename(
            "merged", partition, bucket_index=None,
        ),
    )
    parquet_files = sorted(fs_utils.glob(
        fs_utils.join(variants_dir, "*.parquet"),
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
            row_group_size=row_group_size,
            parquet_version=parquet_version)
