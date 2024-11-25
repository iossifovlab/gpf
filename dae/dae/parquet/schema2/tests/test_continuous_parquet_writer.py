# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import pathlib

import pyarrow.parquet as pq

from dae.parquet.schema2.parquet_io import ContinuousParquetFileWriter


def test_empty_continuous_parquet_writer(tmp_path: pathlib.Path) -> None:
    test_parquet = str(tmp_path / "test.parquet")
    writer = ContinuousParquetFileWriter(
        test_parquet,
        annotation_schema=[],
        schema="schema_summary",
    )

    writer.close()
    assert os.path.exists(test_parquet)

    table = pq.read_table(test_parquet)
    assert len(table) == 0
