# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest_mock
from dae.parquet.schema2.loader import MultiReader, ParquetLoader


def test_contigs(acgt_study_partitioned: str) -> None:
    loader = ParquetLoader.load_from_dir(acgt_study_partitioned)
    assert loader.contigs == {"chr1": 100, "chr2": 100, "chr3": 100}


def test_fetch_variants_closes_files_on_destruction(
    mocker: pytest_mock.MockerFixture,
    t4c8_study_partitioned: str,
) -> None:
    mocker.spy(MultiReader, "close")
    loader = ParquetLoader.load_from_dir(t4c8_study_partitioned)
    iterator = loader.fetch_variants()
    next(iterator)  # get at least one variant
    del iterator
    assert MultiReader.close.call_count == 2  # type: ignore


def test_sj_index_is_correctly_read(
    t4c8_study_partitioned: str,
) -> None:
    loader = ParquetLoader.load_from_dir(t4c8_study_partitioned)
    vs = list(loader.fetch_summary_variants())
    sj_indices = [
        allele.attributes["sj_index"]
        for v in vs
        for allele in v.alt_alleles
    ]
    assert sj_indices == [
        1000000000000000001,
        1000000000000000002,
        1000000000000010001,
        1000000000000020001,
        1000000000000020002,
        1000000000000030001,
        1000000000000030002,
        1000000000000040001,
        1000000000000040002,
        1000000000000050001,
        1000000000000050002,
    ]
