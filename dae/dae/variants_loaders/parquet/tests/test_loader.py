# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest_mock

from dae.variants_loaders.parquet.loader import MultiReader, ParquetLoader


def test_contigs(acgt_study_partitioned: str) -> None:
    loader = ParquetLoader(acgt_study_partitioned)
    assert loader.contigs == {"chr1": 100, "chr2": 100, "chr3": 100}


def test_fetch_variants_closes_files_on_destruction(
    mocker: pytest_mock.MockerFixture,
    t4c8_study_partitioned: str,
) -> None:
    mocker.spy(MultiReader, "close")
    loader = ParquetLoader(t4c8_study_partitioned)
    iterator = loader.fetch_variants()
    next(iterator)  # get at least one variant
    del iterator
    assert MultiReader.close.call_count == 2  # type: ignore
