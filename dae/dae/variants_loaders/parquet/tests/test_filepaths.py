# pylint: disable=W0621,C0114,C0116,W0212,W0613
import os
from dae.utils.regions import Region
from dae.variants_loaders.parquet.loader import ParquetLoader


def test_get_pq_filepaths_nonpartitioned(
    t4c8_study_nonpartitioned: str
) -> None:
    loader = ParquetLoader(t4c8_study_nonpartitioned)
    summary_filepaths, family_filepaths = loader.get_pq_filepaths()
    assert list(map(os.path.basename, summary_filepaths)) == [
        "summary_bucket_index_100000.parquet"
    ]
    assert list(map(os.path.basename, family_filepaths)) == [
        "family_bucket_index_100000.parquet"
    ]


def test_get_pq_filepaths_partitioned(
    t4c8_study_partitioned: str
) -> None:
    loader = ParquetLoader(t4c8_study_partitioned)
    summary_filepaths, family_filepaths = loader.get_pq_filepaths()
    assert set(map(os.path.basename, summary_filepaths)) == {
        "summary_region_bin_chr1_0_frequency_bin_1_coding_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "summary_region_bin_chr1_0_frequency_bin_2_coding_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "summary_region_bin_chr1_0_frequency_bin_3_coding_bin_1_bucket_index_100000.parquet",  # noqa: E501
        "summary_region_bin_chr1_0_frequency_bin_3_coding_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "summary_region_bin_chr1_1_frequency_bin_1_coding_bin_1_bucket_index_100000.parquet",  # noqa: E501
        "summary_region_bin_chr1_1_frequency_bin_2_coding_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "summary_region_bin_chr1_1_frequency_bin_2_coding_bin_1_bucket_index_100000.parquet",  # noqa: E501
    }
    assert set(map(os.path.basename, family_filepaths)) == {
        "family_region_bin_chr1_0_frequency_bin_1_coding_bin_0_family_bin_1_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_0_frequency_bin_2_coding_bin_0_family_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_0_frequency_bin_2_coding_bin_0_family_bin_1_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_0_frequency_bin_3_coding_bin_0_family_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_0_frequency_bin_3_coding_bin_0_family_bin_1_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_0_frequency_bin_3_coding_bin_1_family_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_0_frequency_bin_3_coding_bin_1_family_bin_1_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_1_frequency_bin_1_coding_bin_1_family_bin_1_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_1_frequency_bin_2_coding_bin_0_family_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_1_frequency_bin_2_coding_bin_0_family_bin_1_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_1_frequency_bin_2_coding_bin_1_family_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_1_frequency_bin_2_coding_bin_1_family_bin_1_bucket_index_100000.parquet",  # noqa: E501
    }


def test_get_pq_filepaths_partitioned_region(
    t4c8_study_partitioned: str
) -> None:
    loader = ParquetLoader(t4c8_study_partitioned)

    region = Region("chr1", 1, 100)
    summary_filepaths, family_filepaths = loader.get_pq_filepaths(region)
    assert set(map(os.path.basename, summary_filepaths)) == {
        "summary_region_bin_chr1_0_frequency_bin_1_coding_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "summary_region_bin_chr1_0_frequency_bin_2_coding_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "summary_region_bin_chr1_0_frequency_bin_3_coding_bin_1_bucket_index_100000.parquet",  # noqa: E501
        "summary_region_bin_chr1_0_frequency_bin_3_coding_bin_0_bucket_index_100000.parquet",  # noqa: E501
    }
    assert set(map(os.path.basename, family_filepaths)) == {
        "family_region_bin_chr1_0_frequency_bin_1_coding_bin_0_family_bin_1_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_0_frequency_bin_2_coding_bin_0_family_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_0_frequency_bin_2_coding_bin_0_family_bin_1_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_0_frequency_bin_3_coding_bin_0_family_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_0_frequency_bin_3_coding_bin_0_family_bin_1_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_0_frequency_bin_3_coding_bin_1_family_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_0_frequency_bin_3_coding_bin_1_family_bin_1_bucket_index_100000.parquet",  # noqa: E501
    }

    region = Region("chr1", 101, 200)
    summary_filepaths, family_filepaths = loader.get_pq_filepaths(region)
    assert set(map(os.path.basename, summary_filepaths)) == {
        "summary_region_bin_chr1_1_frequency_bin_1_coding_bin_1_bucket_index_100000.parquet",  # noqa: E501
        "summary_region_bin_chr1_1_frequency_bin_2_coding_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "summary_region_bin_chr1_1_frequency_bin_2_coding_bin_1_bucket_index_100000.parquet",  # noqa: E501
    }
    assert set(map(os.path.basename, family_filepaths)) == {
        "family_region_bin_chr1_1_frequency_bin_1_coding_bin_1_family_bin_1_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_1_frequency_bin_2_coding_bin_0_family_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_1_frequency_bin_2_coding_bin_0_family_bin_1_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_1_frequency_bin_2_coding_bin_1_family_bin_0_bucket_index_100000.parquet",  # noqa: E501
        "family_region_bin_chr1_1_frequency_bin_2_coding_bin_1_family_bin_1_bucket_index_100000.parquet",  # noqa: E501
    }
