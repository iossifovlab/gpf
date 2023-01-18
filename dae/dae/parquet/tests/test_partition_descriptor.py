# pylint: disable=W0621,C0114,C0116,W0212,W0613
import textwrap

from dae.testing import setup_directories
from dae.parquet.partition_descriptor import PartitionDescriptor


def test_parse_toml_partition_description(tmp_path):
    setup_directories(
        tmp_path / "partition_description.conf",
        textwrap.dedent("""
          [region_bin]
          chromosomes = foo,bar
          region_length = 8

          [family_bin]
          family_bin_size = 2

          [frequency_bin]
          rare_boundary = 50
        """)
    )
    pd_filename = tmp_path / "partition_description.conf"
    pdesc = PartitionDescriptor.parse(pd_filename)

    assert pdesc.chromosomes == ["foo", "bar"]
    assert pdesc.region_length == 8
    assert pdesc.family_bin_size == 2
    assert pdesc.rare_boundary == 50


def test_parse_yaml_partition_description(tmp_path):
    setup_directories(
        tmp_path / "partition_description.yaml",
        textwrap.dedent("""
            region_bin:
              chromosomes: foo,bar
              region_length: 8
            family_bin:
              family_bin_size: 2
            frequency_bin:
              rare_boundary: 50
        """)
    )
    pd_filename = tmp_path / "partition_description.yaml"
    pdesc = PartitionDescriptor.parse(pd_filename)

    assert pdesc.chromosomes == ["foo", "bar"]
    assert pdesc.region_length == 8
    assert pdesc.family_bin_size == 2
    assert pdesc.rare_boundary == 50


def test_partition_directory():
    assert PartitionDescriptor.partition_directory(
        "work", [("region_bin", "1")]) == "work/region_bin=1"
    assert PartitionDescriptor.partition_directory(
        "s3://work", [("region_bin", "1")]) == "s3://work/region_bin=1"


def test_partition_filename():
    assert PartitionDescriptor.partition_filename(
        "summary", [("region_bin", "1")], 1) == \
        "summary_region_bin_1_bucket_index_000001.parquet"
