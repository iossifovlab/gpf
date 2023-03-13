# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
import pytest
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
from dae.parquet.helpers import url_to_pyarrow_fs, merge_parquets


def test_url_to_pyarrow_fs():
    filename = "path/to/some/file.txt"
    fs, path = url_to_pyarrow_fs(filename)
    assert fs is None
    assert path == filename


def test_url_to_pyarrow_fs_s3_url():
    filename = "s3://bucket/file.txt"
    fs, path = url_to_pyarrow_fs(filename)
    assert isinstance(fs, pa.fs.PyFileSystem)
    assert path == "bucket/file.txt"


def test_merge_parquets(tmpdir):
    full_data = pd.DataFrame({
        "n_legs": [2, 2, 4, 4, 5, 100],
        "animal": [
            "Flamingo", "Parrot", "Dog", "Horse", "Brittle stars", "Centipede"
        ]
    })

    in_files = []
    for i in range(0, len(full_data), 2):
        table = pa.table(full_data.iloc[i:i + 2])
        in_files.append(str(tmpdir / f"p{i}.parquet"))
        writer = pq.ParquetWriter(in_files[-1], table.schema)
        writer.write_table(table)
        writer.close()

    out_file = str(tmpdir / "merged.parquet")
    merge_parquets(in_files, out_file)

    merged = pq.ParquetFile(out_file)
    assert merged.schema_arrow == table.schema
    data = merged.read().to_pandas()
    assert (data == full_data).all().all()

    # assert input files get deleted
    for in_file in in_files:
        assert not os.path.exists(in_file)


def test_merge_parquets_single_file(tmpdir):
    table = pa.table({
        "n_legs": [2, 2, 4, 4, 5, 100],
        "animal": [
            "Flamingo", "Parrot", "Dog", "Horse", "Brittle stars", "Centipede"
        ]
    })
    in_file = str(tmpdir / "in.parquet")
    writer = pq.ParquetWriter(in_file, table.schema)
    writer.write_table(table)
    writer.close()

    out_file = str(tmpdir / "out.parquet")
    merge_parquets([in_file], out_file)

    merged = pq.ParquetFile(out_file)
    assert merged.schema_arrow == table.schema
    data = merged.read().to_pandas()
    assert (data == table.to_pandas()).all().all()


def test_merge_parquets_no_files():
    with pytest.raises(Exception):
        merge_parquets([], "out.parquet")
    assert not os.path.exists("out.parquet")


def test_merge_parquets_broken_input_file(tmpdir):
    table = pa.table({
        "n_legs": [2, 2, 4, 4, 5, 100],
        "animal": [
            "Flamingo", "Parrot", "Dog", "Horse", "Brittle stars", "Centipede"
        ]
    })
    writer = pq.ParquetWriter(str(tmpdir / "p1.parquet"), table.schema)
    writer.write_table(table)
    writer.close()

    with open(str(tmpdir / "p2.parquet"), "wt") as file:
        file.write("This is not a parquet file.")

    in_files = [str(tmpdir / "p1.parquet"), str(tmpdir / "p2.parquet")]
    out_file = str(tmpdir / "merged.parquet")
    with pytest.raises(Exception):
        merge_parquets(in_files, out_file)

    # assert no partial output file is left behind in case of error
    assert not os.path.exists(out_file)
