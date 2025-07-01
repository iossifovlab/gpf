# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import random

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
        "n_legs": [2, 2, 4, 4, 5, 100],
        "animal": [
            "Flamingo", "Parrot", "Dog", "Horse", "Brittle stars", "Centipede",
        ],
    })

    table = None
    for i in range(0, len(full_data), 2):
        table = pa.table(full_data.iloc[i:i + 2])
        in_file = str(tmp_path / f"p{i}.parquet")
        writer = pq.ParquetWriter(
            in_file,
            table.schema,
        )
        writer.write_table(table)
        writer.close()

    return tmp_path


@pytest.mark.parametrize("row_group_size, expected", [
    (50_000, 1),
    (2, 3),
    (3, 2),
    (4, 2),
    (5, 1),
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
    assert len(data) == 6

    assert merged.num_row_groups == expected


@pytest.fixture
def multi_parquet_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    """Fixture to create a temporary directory for parquet files."""

    full_data = pd.DataFrame({
        "value": range(8),
        "label": [f"l0{i}" for i in range(8)],
    })

    table = None
    for i in range(0, len(full_data), 2):
        for j in (0, 1):
            table = pa.table(full_data.iloc[i + j:i + j + 1])
            (tmp_path / f"d{i}" / f"d{j}").mkdir(parents=True, exist_ok=True)
            in_file = str(tmp_path / f"d{i}" / f"d{j}" / f"p{i}_{j}.parquet")
            writer = pq.ParquetWriter(
                in_file,
                table.schema,
            )
            writer.write_table(table)
            writer.close()

    return tmp_path


@pytest.mark.parametrize("row_group_size, expected", [
    (50_000, 1),
    (2, 4),
    (3, 3),
    (4, 2),
    (5, 2),
    (8, 1),
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
    assert len(data) == 8
    assert data.value.to_numpy().tolist() == list(range(8))
    assert data.label.to_numpy().tolist() == [f"l0{i}" for i in range(8)]


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
        multi_parquet_dir, out_file, row_group_size=2)

    merged = pq.ParquetFile(out_file)
    assert merged.num_row_groups == 4

    data = merged.read().to_pandas()
    assert len(data) == 8
    assert data.value.to_numpy().tolist() == list(range(8))
    assert data.label.to_numpy().tolist() == [f"l0{i}" for i in range(8)]


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

    data = merged.read().to_pandas()
    assert len(data) == 6

    assert spy.call_count == 1
    assert not any("merged_parquet" in fn for fn in spy.call_args[0][0])
