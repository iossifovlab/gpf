# pylint: disable=W0621,C0114,C0115,C0116,W0212,W0613
import pathlib

import pyarrow.parquet as pq
import pytest
import pytest_mock
from dae.parquet.partition_descriptor import (
    PartitionDescriptor,
)
from dae.parquet.schema2.processing_pipeline import (
    VariantsLoaderBatchSource,
    VariantsLoaderSource,
)
from dae.parquet.schema2.variants_parquet_writer import (
    VariantsParquetWriter,
)
from dae.variants_loaders.raw.loader import (
    VariantsGenotypesLoader,
)


def test_variants_parquet_writer_simple(
    study_1_loader: VariantsGenotypesLoader,
    tmp_path: pathlib.Path,
) -> None:
    """Test the variants parquet writer."""
    variants_source = VariantsLoaderSource(study_1_loader)
    partition_descriptor = PartitionDescriptor()
    output_path = tmp_path / "output"
    variants_writer = VariantsParquetWriter(
        output_path,
        annotation_schema=[],
        partition_descriptor=partition_descriptor,
    )
    variants_writer.consume(variants_source.fetch())
    variants_writer.close()

    assert variants_writer.summary_index == 6
    assert variants_writer.family_index == 12

    assert output_path.exists()
    assert output_path.is_dir()
    assert (output_path / "family").exists()
    assert (output_path / "summary").exists()


@pytest.mark.parametrize(
    "batch_size",
    [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        500,
    ],
)
def test_variants_parquet_writer_batches_simple(
    study_1_loader: VariantsGenotypesLoader,
    tmp_path: pathlib.Path,
    batch_size: int,
) -> None:
    """Test the variants parquet writer."""
    variants_source = VariantsLoaderBatchSource(
        study_1_loader, batch_size=batch_size)
    partition_descriptor = PartitionDescriptor()
    output_path = tmp_path / "output"
    variants_writer = VariantsParquetWriter(
        output_path,
        annotation_schema=[],
        partition_descriptor=partition_descriptor,
    )
    variants_writer.consume_batches(variants_source.fetch_batches())
    variants_writer.close()

    assert variants_writer.summary_index == 6
    assert variants_writer.family_index == 12

    assert output_path.exists()
    assert output_path.is_dir()
    assert (output_path / "family").exists()
    assert (output_path / "summary").exists()


@pytest.mark.parametrize(
    "row_group_size, expected_row_groups",
    [
        (1, 11),
        (2, 6),
        (3, 4),
        (4, 3),
        (5, 3),
        (6, 2),
        (7, 2),
        (500, 1),
    ],
)
def test_variants_parquet_writer_row_group_size(
    study_1_loader: VariantsGenotypesLoader,
    tmp_path: pathlib.Path,
    row_group_size: int,
    expected_row_groups: int,
) -> None:
    """Test the variants parquet writer."""

    variants_source = VariantsLoaderSource(study_1_loader)
    partition_descriptor = PartitionDescriptor()
    output_path = tmp_path / "output"
    variants_writer = VariantsParquetWriter(
        output_path,
        annotation_schema=[],
        partition_descriptor=partition_descriptor,
        row_group_size=row_group_size,
    )
    variants_writer.consume(variants_source.fetch())
    variants_writer.close()

    assert variants_writer.summary_index == 6
    assert variants_writer.family_index == 12

    assert output_path.exists()
    assert output_path.is_dir()
    assert (output_path / "summary").exists()
    summary_path = output_path / "summary"
    assert summary_path.exists()
    assert summary_path.is_dir()
    parquet_path = summary_path / "summary_bucket_index_000001.parquet"
    assert parquet_path.exists()
    assert parquet_path.is_file()

    pq_metadata = pq.read_metadata(parquet_path)
    assert pq_metadata.num_rows == 11
    assert pq_metadata.num_row_groups == expected_row_groups


def test_variants_parquet_writer_no_blob(
    study_1_loader: VariantsGenotypesLoader,
    tmp_path: pathlib.Path,
    mocker: pytest_mock.MockerFixture,
) -> None:
    """Test the variants parquet writer."""

    mocker.patch(
        "dae.parquet.schema2.serializers."
        "FamilyAlleleParquetSerializer.blob_column",
        return_value=None,
    )
    mocker.patch(
        "dae.parquet.schema2.serializers."
        "SummaryAlleleParquetSerializer.blob_column",
        return_value=None,
    )
    variants_source = VariantsLoaderSource(study_1_loader)
    partition_descriptor = PartitionDescriptor()
    output_path = tmp_path / "output"

    with VariantsParquetWriter(
        output_path,
        annotation_schema=[],
        partition_descriptor=partition_descriptor,
    ) as variants_writer:
        variants_writer.consume(variants_source.fetch())

    assert variants_writer.summary_index == 6
    assert variants_writer.family_index == 12

    summary_path = output_path / "summary"
    parquet_path = summary_path / "summary_bucket_index_000001.parquet"

    pq_metadata = pq.read_metadata(parquet_path)
    assert pq_metadata.num_rows == 11
    assert pq_metadata.num_columns == 21
    assert pq_metadata.num_row_groups == 1
    blob_column = pq_metadata.row_group(0).column(20)
    assert blob_column.compression == "SNAPPY"


def test_variants_parquet_writer_default_blob(
    study_1_loader: VariantsGenotypesLoader,
    tmp_path: pathlib.Path,
) -> None:

    variants_source = VariantsLoaderSource(study_1_loader)
    partition_descriptor = PartitionDescriptor()
    output_path = tmp_path / "output"

    with VariantsParquetWriter(
                output_path,
                annotation_schema=[],
                partition_descriptor=partition_descriptor,
            ) as variants_writer:
        variants_writer.consume(variants_source.fetch())

    assert variants_writer.summary_index == 6
    assert variants_writer.family_index == 12

    summary_path = output_path / "summary"
    parquet_path = summary_path / "summary_bucket_index_000001.parquet"

    pq_metadata = pq.read_metadata(parquet_path)
    assert pq_metadata.num_rows == 11
    assert pq_metadata.num_columns == 21
    assert pq_metadata.num_row_groups == 1
    blob_column = pq_metadata.row_group(0).column(20)
    assert blob_column.compression == "ZSTD"
