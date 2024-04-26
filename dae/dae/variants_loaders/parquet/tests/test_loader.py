# pylint: disable=W0621,C0114,C0116,W0212,W0613
from dae.variants_loaders.parquet.loader import ParquetLoader


def test_contigs(acgt_study_partitioned: str) -> None:
    loader = ParquetLoader(acgt_study_partitioned)
    assert loader.contigs == ["chr1", "chr2", "chr3"]
