# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import pathlib
import textwrap

import pyarrow as pa
import pyarrow.parquet as pq

from dae.parquet.parquet_writer import merge_variants_parquets
from dae.parquet.partition_descriptor import PartitionDescriptor


def test_merge_parquets(tmp_path: pathlib.Path) -> None:
    pd_content = textwrap.dedent("""
        region_bin:
            chromosomes: foo,bar
            region_length: 8
        family_bin:
            family_bin_size: 2
    """)
    part_desc = PartitionDescriptor.parse_string(pd_content, "yaml")

    def write_parquets() -> None:
        pq.write_table(
            pa.table({
                "index": [1, 2, 3],
                "prop": ["a", "b", "c"],
            }),
            str(tmp_path / "p1.parquet"),
            compression={"index": "snappy", "prop": "zstd"},
        )
        pq.write_table(
            pa.table({
                "index": [4, 5, 6],
                "prop": ["d", "e", "f"],
            }),
            str(tmp_path / "p2.parquet"),
            compression={"index": "snappy", "prop": "zstd"},
        )

    # run and assert files are merged
    write_parquets()
    merge_variants_parquets(
        part_desc, str(tmp_path),
        [("region_bin", "foo_0"), ("family_bin", "1")],
    )
    out_files = os.listdir(str(tmp_path))
    assert len(out_files) == 1

    # run again and assert dir is unchanged
    merge_variants_parquets(
        part_desc, str(tmp_path),
        [("region_bin", "foo_0"), ("family_bin", "1")],
    )
    out_files = os.listdir(str(tmp_path))
    assert len(out_files) == 1

    # generate files and run again
    write_parquets()
    merge_variants_parquets(
        part_desc, str(tmp_path),
        [("region_bin", "foo_0"), ("family_bin", "1")],
    )
    out_files = os.listdir(str(tmp_path))
    assert len(out_files) == 1
    out_parquet = pq.ParquetFile(tmp_path / out_files[0])
    assert out_parquet.num_row_groups == 1
    row_group = out_parquet.metadata.row_group(0)
    assert row_group.column(0).compression == "SNAPPY"
    assert row_group.column(1).compression == "ZSTD"
