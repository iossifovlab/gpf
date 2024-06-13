# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os

from dae.utils.regions import Region
from dae.variants_loaders.parquet.loader import ParquetLoader


def test_get_summary_pq_filepaths_nonpartitioned(
    t4c8_study_nonpartitioned: str,
) -> None:
    loader = ParquetLoader(t4c8_study_nonpartitioned)
    filepaths = next(loader.get_summary_pq_filepaths())
    assert list(map(os.path.basename, filepaths)) == [
        "summary_bucket_index_100000.parquet",
    ]


def test_get_summary_pq_filepaths_partitioned(
    t4c8_study_partitioned: str,
) -> None:
    loader = ParquetLoader(t4c8_study_partitioned)
    filepaths = list(loader.get_summary_pq_filepaths())
    assert len(filepaths) == 2

    first = set(map(os.path.basename, filepaths[0]))
    second = set(map(os.path.basename, filepaths[1]))
    if "chr1_0" in filepaths[1][0]:
        first, second = second, first

    assert first == {
        "summary_region_bin_chr1_0_frequency_bin_1_coding_bin_0_bucket_index_100000.parquet",
        "summary_region_bin_chr1_0_frequency_bin_2_coding_bin_0_bucket_index_100000.parquet",
        "summary_region_bin_chr1_0_frequency_bin_3_coding_bin_1_bucket_index_100000.parquet",
        "summary_region_bin_chr1_0_frequency_bin_3_coding_bin_0_bucket_index_100000.parquet",
    }
    assert second == {
        "summary_region_bin_chr1_1_frequency_bin_1_coding_bin_1_bucket_index_100000.parquet",
        "summary_region_bin_chr1_1_frequency_bin_2_coding_bin_0_bucket_index_100000.parquet",
        "summary_region_bin_chr1_1_frequency_bin_2_coding_bin_1_bucket_index_100000.parquet",
    }


def test_get_summary_pq_filepaths_partitioned_region(
    t4c8_study_partitioned: str,
) -> None:
    loader = ParquetLoader(t4c8_study_partitioned)
    region = Region("chr1", 1, 100)
    filepaths = next(loader.get_summary_pq_filepaths(region))
    assert set(map(os.path.basename, filepaths)) == {
        "summary_region_bin_chr1_0_frequency_bin_1_coding_bin_0_bucket_index_100000.parquet",
        "summary_region_bin_chr1_0_frequency_bin_2_coding_bin_0_bucket_index_100000.parquet",
        "summary_region_bin_chr1_0_frequency_bin_3_coding_bin_1_bucket_index_100000.parquet",
        "summary_region_bin_chr1_0_frequency_bin_3_coding_bin_0_bucket_index_100000.parquet",
    }

    region = Region("chr1", 101, 200)
    filepaths = next(loader.get_summary_pq_filepaths(region))
    assert set(map(os.path.basename, filepaths)) == {
        "summary_region_bin_chr1_1_frequency_bin_1_coding_bin_1_bucket_index_100000.parquet",
        "summary_region_bin_chr1_1_frequency_bin_2_coding_bin_0_bucket_index_100000.parquet",
        "summary_region_bin_chr1_1_frequency_bin_2_coding_bin_1_bucket_index_100000.parquet",
    }


def test_get_family_filepaths_case_a(t4c8_study_partitioned: str) -> None:
    loader = ParquetLoader(t4c8_study_partitioned)
    summary_path = os.path.join(
        t4c8_study_partitioned,
        "summary/region_bin=chr1_1/frequency_bin=1/coding_bin=1/summary_region_bin_chr1_1_frequency_bin_1_coding_bin_1_bucket_index_100000.parquet",
    )
    family_path = os.path.join(
        t4c8_study_partitioned,
        "family/region_bin=chr1_1/frequency_bin=1/coding_bin=1/family_bin=1/family_region_bin_chr1_1_frequency_bin_1_coding_bin_1_family_bin_1_bucket_index_100000.parquet",
    )
    assert loader.get_family_pq_filepaths(summary_path) == [family_path,]


def test_get_family_filepaths_case_b(t4c8_study_partitioned: str) -> None:
    loader = ParquetLoader(t4c8_study_partitioned)
    summary_path = os.path.join(
        t4c8_study_partitioned,
        "summary/region_bin=chr1_1/frequency_bin=2/coding_bin=0/summary_region_bin_chr1_1_frequency_bin_2_coding_bin_0_bucket_index_100000.parquet",
    )
    family_path_1 = os.path.join(
        t4c8_study_partitioned,
        "family/region_bin=chr1_1/frequency_bin=2/coding_bin=0/family_bin=0/family_region_bin_chr1_1_frequency_bin_2_coding_bin_0_family_bin_0_bucket_index_100000.parquet",
    )
    family_path_2 = os.path.join(
        t4c8_study_partitioned,
        "family/region_bin=chr1_1/frequency_bin=2/coding_bin=0/family_bin=1/family_region_bin_chr1_1_frequency_bin_2_coding_bin_0_family_bin_1_bucket_index_100000.parquet",
    )
    assert sorted(loader.get_family_pq_filepaths(summary_path)) \
         == [family_path_1, family_path_2]
