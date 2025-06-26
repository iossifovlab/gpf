# pylint: disable=W0621,C0114,C0115,C0116,W0212,W0613
import pathlib

import pytest
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
