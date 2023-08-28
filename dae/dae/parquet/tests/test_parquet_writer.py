# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import pathlib

import textwrap
import pyarrow as pa
import pyarrow.parquet as pq

from dae.parquet.partition_descriptor import PartitionDescriptor
from dae.parquet.parquet_writer import ParquetWriter


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
                "prop": ["a", "b", "c"]
            }),
            str(tmp_path / "p1.parquet")
        )
        pq.write_table(
            pa.table({
                "index": [4, 5, 6],
                "prop": ["d", "e", "f"]
            }),
            str(tmp_path / "p2.parquet")
        )

    # run and assert files are merged
    write_parquets()
    ParquetWriter.merge_parquets(
        part_desc, str(tmp_path),
        [("region_bin", "foo_0"), ("family_bin", "1")]
    )
    out_files = os.listdir(str(tmp_path))
    assert len(out_files) == 1

    # run again and assert dir is unchanged
    ParquetWriter.merge_parquets(
        part_desc, str(tmp_path),
        [("region_bin", "foo_0"), ("family_bin", "1")]
    )
    out_files = os.listdir(str(tmp_path))
    assert len(out_files) == 1

    # generate files and run again
    write_parquets()
    ParquetWriter.merge_parquets(
        part_desc, str(tmp_path),
        [("region_bin", "foo_0"), ("family_bin", "1")]
    )
    out_files = os.listdir(str(tmp_path))
    assert len(out_files) == 1
