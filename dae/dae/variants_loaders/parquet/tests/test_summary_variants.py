# pylint: disable=W0621,C0114,C0116,W0212,W0613
from dae.utils.regions import Region
from dae.variants_loaders.parquet.loader import ParquetLoader


def test_fetch_summary_variants_nonpartitioned(
    t4c8_study_nonpartitioned: str,
) -> None:
    loader = ParquetLoader(t4c8_study_nonpartitioned)
    vs = list(loader.fetch_summary_variants())
    assert len(vs) == 3


def test_fetch_summary_variants_partitioned(
    t4c8_study_partitioned: str,
) -> None:
    loader = ParquetLoader(t4c8_study_partitioned)
    vs = list(loader.fetch_summary_variants())
    assert len(vs) == 6


def test_fetch_summary_variants_nonpartitioned_region(
    t4c8_study_nonpartitioned: str,
) -> None:
    loader = ParquetLoader(t4c8_study_nonpartitioned)
    vs = list(loader.fetch_summary_variants(region=Region("chr1", 119, 119)))
    assert len(vs) == 1
    vs = list(loader.fetch_summary_variants(region=Region("chr1", 119, 122)))
    assert len(vs) == 2


def test_fetch_summary_variants_partitioned_region(
    t4c8_study_partitioned: str,
) -> None:
    loader = ParquetLoader(t4c8_study_partitioned)
    vs = list(loader.fetch_summary_variants(region=Region("chr1", 1, 89)))
    assert len(vs) == 2
    vs = list(loader.fetch_summary_variants(region=Region("chr1", 90, 200)))
    assert len(vs) == 4


def test_fetch_summary_variants_count_acgt(
    acgt_study_partitioned: str,
) -> None:
    loader = ParquetLoader(acgt_study_partitioned)
    assert len(list(loader.fetch_summary_variants())) == 9
    assert len(
        list(loader.fetch_summary_variants(region=Region("chr1", 1, 100)))) == 3
    assert len(
        list(loader.fetch_summary_variants(region=Region("chr2", 1, 100)))) == 3
    assert len(
        list(loader.fetch_summary_variants(region=Region("chr3", 1, 100)))) == 3


def test_fetch_summary_variants_pedigree_only(
    t4c8_study_pedigree_only: str,
) -> None:
    loader = ParquetLoader(t4c8_study_pedigree_only)
    assert len(list(loader.fetch_summary_variants())) == 0
