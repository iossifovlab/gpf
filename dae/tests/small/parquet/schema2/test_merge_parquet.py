# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import random

import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import pytest_mock
from dae.parquet.schema2 import merge_parquet
from dae.parquet.schema2.merge_parquet import merge_parquet_directory
from dae.utils import fs_utils


@pytest.fixture
def parquet_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    """Fixture to create a temporary directory for parquet files."""

    full_data = pd.DataFrame({
        "n_count": range(20_000),
        "s_count": [f"s{i}" for i in range(20_000)],
    })

    table = None
    step = 5_000
    for i in range(0, len(full_data), step):
        table = pa.table(full_data.iloc[i:i + step])
        in_file = str(tmp_path / f"p{i:09}.parquet")
        writer = pq.ParquetWriter(
            in_file,
            table.schema,
        )
        writer.write_table(table)
        writer.close()

    return tmp_path


@pytest.mark.parametrize("row_group_size, expected", [
    (5_000, 4),
    (10000, 2),
    (20000, 1),
    (50_000, 1),
])
def test_merge_parquets(
    parquet_dir: pathlib.Path,
    row_group_size: int, expected: int,
) -> None:

    out_file = str(parquet_dir / "merged.parquet")
    merge_parquet_directory(
        parquet_dir, out_file, row_group_size=row_group_size)

    merged = pq.ParquetFile(out_file)
    data = merged.read().to_pandas()
    assert len(data) == 20_000

    assert merged.num_row_groups == expected

    assert data.n_count.to_numpy().tolist() == list(range(20_000))
    assert data.s_count.to_numpy().tolist() == [f"s{i}" for i in range(20_000)]


@pytest.fixture
def multi_parquet_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    """Fixture to create a temporary directory with parquet files."""

    full_data = pd.DataFrame({
        "value": range(20_000),
        "label": [f"l0{i}" for i in range(20_000)],
    })

    step = 2_000
    table = None
    for i in range(0, len(full_data), 2 * step):
        for j in range(2):
            print(i + j * step, i + (j + 1) * step)
            table = pa.table(
                full_data.iloc[i + j * step:i + (j + 1) * step])
            dir_path = tmp_path / f"d{i:09}" / f"d{j:09}"
            dir_path.mkdir(parents=True, exist_ok=True)
            in_file = str(
                dir_path / f"p{i:09}_{j:09}.parquet")
            writer = pq.ParquetWriter(
                in_file,
                table.schema,
            )
            writer.write_table(table)
            writer.close()

    return tmp_path


@pytest.mark.parametrize("row_group_size, expected", [
    (50_000, 1),
    (5_000, 4),
    (10000, 2),
    (20000, 1),
])
def test_merge_multi_parquets(
    multi_parquet_dir: pathlib.Path,
    row_group_size: int, expected: int,
) -> None:

    out_file = str(multi_parquet_dir / "merged.parquet")
    merge_parquet_directory(
        multi_parquet_dir, out_file, row_group_size=row_group_size)

    merged = pq.ParquetFile(out_file)
    assert merged.num_row_groups == expected

    data = merged.read().to_pandas()
    assert len(data) == 20_000
    assert data.value.to_numpy().tolist() == list(range(20_000))
    assert data.label.to_numpy().tolist() == [f"l0{i}" for i in range(20_000)]


def test_merge_multi_parquets_randomized(
        multi_parquet_dir: pathlib.Path,
        mocker: pytest_mock.MockerFixture,
) -> None:
    """Test merging multiple parquet files with randomized order."""
    # Mock the sorted function to return a randomized order

    def randomized_glob() -> list[str]:
        files = fs_utils.glob(str(multi_parquet_dir / "**/*.parquet"))
        return sorted(files, key=lambda _: random.random())  # noqa: S311

    mocker.patch(
        "dae.utils.fs_utils.glob",
        return_value=randomized_glob())

    out_file = str(multi_parquet_dir / "merged.parquet")
    merge_parquet_directory(
        multi_parquet_dir, out_file, row_group_size=5000)

    merged = pq.ParquetFile(out_file)
    assert merged.num_row_groups == 4

    data = merged.read().to_pandas()
    assert len(data) == 20000
    assert data.value.to_numpy().tolist() == list(range(20_000))
    assert data.label.to_numpy().tolist() == [f"l0{i}" for i in range(20_000)]


def test_merge_parquet_directory_no_files(tmp_path: pathlib.Path) -> None:
    """Test merging an empty directory."""
    out_file = str(tmp_path / "merged.parquet")
    merge_parquet_directory(tmp_path, out_file)

    assert not pathlib.Path(out_file).exists()


def test_merge_parquet_directory_with_output_in_input(
    parquet_dir: pathlib.Path,
    mocker: pytest_mock.MockerFixture,
) -> None:
    """Test merging when output file is already in the input directory."""
    out_file = str(parquet_dir / "merged.parquet")
    # Create an empty output file
    pathlib.Path(out_file).touch()
    # Spy on the merge_parquets function to check how it is called
    spy = mocker.spy(merge_parquet, "merge_parquets")

    merge_parquet_directory(parquet_dir, out_file)

    merged = pq.ParquetFile(out_file)
    assert merged.num_row_groups == 1

    assert spy.call_count == 1
    assert not any("merged_parquet" in fn for fn in spy.call_args[0][0])


def test_merge_parquets_broken_input_file(tmp_path: pathlib.Path) -> None:
    table = pa.table({
        "n_legs": [2, 2, 4, 4, 5, 100],
        "animal": [
            "Flamingo", "Parrot", "Dog", "Horse", "Brittle stars", "Centipede",
        ],
    })
    writer = pq.ParquetWriter(
        str(tmp_path / "p1.parquet"),
        table.schema,
    )
    writer.write_table(table)
    writer.close()

    with open(str(tmp_path / "p2.parquet"), "wt") as file:
        file.write("This is not a parquet file.")

    out_file = str(tmp_path / "merged.parquet")
    with pytest.raises(OSError, match="invalid input parquet file"):
        merge_parquet_directory(str(tmp_path), out_file)


@pytest.mark.parametrize("row_group_size, expected", [
    (5_000, 4),
    (10_000, 2),
    (20_000, 1),
    (50_000, 1),
])
def test_explore_merging_parquet_using_duckdb(
    parquet_dir: pathlib.Path,
    row_group_size: int,
    expected: int,
) -> None:
    """Test merging parquet files using DuckDB."""
    out_file = str(parquet_dir / "merged_duckdb.parquet")

    duckdb.from_parquet(str(parquet_dir / "*.parquet")).to_parquet(
        out_file,
        row_group_size=row_group_size,
    )
    merged = pq.ParquetFile(out_file)
    assert merged.num_row_groups == expected

    data = merged.read().to_pandas()
    assert len(data) == 20000
