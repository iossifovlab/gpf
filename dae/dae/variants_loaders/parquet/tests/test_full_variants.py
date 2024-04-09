# pylint: disable=W0621,C0114,C0116,W0212,W0613
from dae.variants_loaders.parquet.loader import ParquetLoader


def test_fetch_variants_count_nonpartitioned(
    t4c8_study_nonpartitioned: str
) -> None:
    loader = ParquetLoader(t4c8_study_nonpartitioned)
    vs = list(loader.fetch_variants())
    # summary variants
    assert len(vs) == 3
    # family variants
    assert sum([len(fvs) for _, fvs in vs]) == 4


def test_fetch_variants_count_partitioned(
    t4c8_study_partitioned: str
) -> None:
    loader = ParquetLoader(t4c8_study_partitioned)
    vs = list(loader.fetch_variants())
    # summary variants
    assert len(vs) == 6
    # family variants
    assert sum([len(fvs) for _, fvs in vs]) == 12


def test_fetch_variants_count_nonpartitioned_region(
    t4c8_study_nonpartitioned: str
) -> None:
    loader = ParquetLoader(t4c8_study_nonpartitioned)
    vs = list(loader.fetch_variants(region="chr1:119"))
    # summary variants
    assert len(vs) == 1
    # family variants
    assert sum([len(fvs) for _, fvs in vs]) == 2

    vs = list(loader.fetch_variants(region="chr1:119-122"))
    # summary variants
    assert len(vs) == 2
    # family variants
    assert sum([len(fvs) for _, fvs in vs]) == 3


def test_fetch_variants_count_partitioned_region(
    t4c8_study_partitioned: str
) -> None:
    loader = ParquetLoader(t4c8_study_partitioned)
    vs = list(loader.fetch_variants(region="chr1:1-89"))
    # summary variants
    assert len(vs) == 2
    # family variants
    assert sum([len(fvs) for _, fvs in vs]) == 4

    vs = list(loader.fetch_variants(region="chr1:90-200"))
    # summary variants
    assert len(vs) == 4
    # family variants
    assert sum([len(fvs) for _, fvs in vs]) == 8
