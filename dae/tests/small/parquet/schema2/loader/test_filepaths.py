# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os

from dae.parquet.schema2.loader import ParquetLoader
from dae.utils.regions import Region


def test_get_summary_pq_filepaths_nonpartitioned(
    t4c8_study_nonpartitioned: str,
) -> None:
    loader = ParquetLoader.load_from_dir(t4c8_study_nonpartitioned)
    filepaths = next(loader.get_summary_pq_filepaths())
    assert list(map(os.path.basename, filepaths)) == [
        "merged_summary_single_bucket.parquet",
    ]


def test_get_summary_pq_filepaths_partitioned(
    t4c8_study_partitioned: str,
) -> None:
    loader = ParquetLoader.load_from_dir(t4c8_study_partitioned)
    filepaths = list(loader.get_summary_pq_filepaths())
    assert len(filepaths) == 2

    first = set(map(os.path.basename, filepaths[0]))
    second = set(map(os.path.basename, filepaths[1]))
    if "chr1_0" in filepaths[1][0]:
        first, second = second, first

    assert first == {
        "merged_region_bin_chr1_0_frequency_bin_1_coding_bin_0.parquet",
        "merged_region_bin_chr1_0_frequency_bin_2_coding_bin_0.parquet",
        "merged_region_bin_chr1_0_frequency_bin_3_coding_bin_1.parquet",
        "merged_region_bin_chr1_0_frequency_bin_3_coding_bin_0.parquet",
    }
    assert second == {
        "merged_region_bin_chr1_1_frequency_bin_2_coding_bin_1.parquet",
        "merged_region_bin_chr1_1_frequency_bin_1_coding_bin_1.parquet",
    }


def test_get_summary_pq_filepaths_partitioned_region(
    t4c8_study_partitioned: str,
) -> None:
    loader = ParquetLoader.load_from_dir(t4c8_study_partitioned)
    region = Region("chr1", 1, 100)
    filepaths = next(loader.get_summary_pq_filepaths(region))
    assert set(map(os.path.basename, filepaths)) == {
        "merged_region_bin_chr1_0_frequency_bin_1_coding_bin_0.parquet",
        "merged_region_bin_chr1_0_frequency_bin_2_coding_bin_0.parquet",
        "merged_region_bin_chr1_0_frequency_bin_3_coding_bin_1.parquet",
        "merged_region_bin_chr1_0_frequency_bin_3_coding_bin_0.parquet",
    }

    region = Region("chr1", 101, 200)
    filepaths = next(loader.get_summary_pq_filepaths(region))
    assert set(map(os.path.basename, filepaths)) == {
        "merged_region_bin_chr1_1_frequency_bin_2_coding_bin_1.parquet",
        "merged_region_bin_chr1_1_frequency_bin_1_coding_bin_1.parquet",
    }


def test_get_family_filepaths_case_a(t4c8_study_partitioned: str) -> None:
    loader = ParquetLoader.load_from_dir(t4c8_study_partitioned)
    summary_path = os.path.join(
        t4c8_study_partitioned,
        "summary/region_bin=chr1_1/frequency_bin=1/coding_bin=1/"
        "merged_region_bin_chr1_1_frequency_bin_1_coding_bin_1.parquet",
    )
    family_path = os.path.join(
        t4c8_study_partitioned,
        "family/region_bin=chr1_1/frequency_bin=1/coding_bin=1/family_bin=1/"
        "merged_region_bin_chr1_1_"
        "frequency_bin_1_coding_bin_1_family_bin_1.parquet",
    )
    assert loader.get_family_pq_filepaths(summary_path) == [family_path]
