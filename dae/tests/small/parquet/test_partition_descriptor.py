# pylint: disable=W0621,C0114,C0116,W0212,W0613
import itertools
import operator
import pathlib
import sys
import textwrap

import pytest
from dae.parquet.partition_descriptor import (
    Partition,
    PartitionDescriptor,
)
from dae.testing import setup_directories
from dae.utils.regions import Region


def test_parse_toml_partition_description(tmp_path: pathlib.Path) -> None:
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

          [coding_bin]
          coding_effect_types = splice-site,missense,frame-shift
        """),
    )
    pd_filename = tmp_path / "partition_description.conf"
    pdesc = PartitionDescriptor.parse(pd_filename)

    assert pdesc.chromosomes == ["foo", "bar"]
    assert pdesc.region_length == 8
    assert pdesc.family_bin_size == 2
    assert pdesc.rare_boundary == 50


def test_parse_toml_partition_description_int_region_bins(
    tmp_path: pathlib.Path,
) -> None:
    setup_directories(
        tmp_path / "partition_description.conf",
        textwrap.dedent("""
          [region_bin]
          chromosomes=foo,bar
          region_length=8
          integer_region_bins=true
          [frequency_bin]
          rare_boundary=50.0
          [coding_bin]
          coding_effect_types=missense,splice-site,frame-shift
          [family_bin]
          family_bin_size=2"""),
    )
    pd_filename = tmp_path / "partition_description.conf"
    pdesc = PartitionDescriptor.parse(pd_filename)

    assert pdesc.chromosomes == ["foo", "bar"]
    assert pdesc.region_length == 8
    assert pdesc.integer_region_bins
    assert pdesc.family_bin_size == 2
    assert pdesc.rare_boundary == 50

    content = pdesc.serialize("conf")
    assert "integer_region_bins=true" in content
    assert (tmp_path / "partition_description.conf").read_text() == content


def test_parse_toml_partition_description_chrom_list(
    tmp_path: pathlib.Path,
) -> None:
    setup_directories(
        tmp_path / "partition_description.conf",
        textwrap.dedent("""
          [region_bin]
          region_length = 8
          chromosomes = [
            "foo", "bar"
          ]
        """),
    )
    pd_filename = tmp_path / "partition_description.conf"
    pdesc = PartitionDescriptor.parse(pd_filename)

    assert pdesc.chromosomes == ["foo", "bar"]
    assert pdesc.region_length == 8


def test_parse_yaml_partition_description(tmp_path: pathlib.Path) -> None:
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
            coding_bin:
              coding_effect_types: splice-site,missense,frame-shift
        """),
    )
    pd_filename = tmp_path / "partition_description.yaml"
    pdesc = PartitionDescriptor.parse(pd_filename)

    assert pdesc.chromosomes == ["foo", "bar"]
    assert pdesc.region_length == 8
    assert pdesc.family_bin_size == 2
    assert pdesc.rare_boundary == 50


def test_parse_yaml_partition_description_int_region_bins(
    tmp_path: pathlib.Path,
) -> None:
    setup_directories(
        tmp_path / "partition_description.yaml",
        textwrap.dedent("""
            region_bin:
              chromosomes: foo,bar
              region_length: 8
              integer_region_bins: true
            frequency_bin:
              rare_boundary: 50.0
            coding_bin:
              coding_effect_types: missense,splice-site,frame-shift
            family_bin:
              family_bin_size: 2"""),
    )
    pd_filename = tmp_path / "partition_description.yaml"
    pdesc = PartitionDescriptor.parse(pd_filename)

    assert pdesc.chromosomes == ["foo", "bar"]
    assert pdesc.region_length == 8
    assert pdesc.integer_region_bins
    assert pdesc.family_bin_size == 2
    assert pdesc.rare_boundary == 50

    content = pdesc.serialize("yaml")
    assert "integer_region_bins: true" in content
    assert (tmp_path / "partition_description.yaml").read_text() == content


def test_parse_yaml_partition_description_chrom_list(
    tmp_path: pathlib.Path,
) -> None:
    setup_directories(
        tmp_path / "partition_description.yaml",
        textwrap.dedent("""
            region_bin:
              chromosomes:
              - foo
              - bar
              region_length: 8
        """),
    )
    pd_filename = tmp_path / "partition_description.yaml"
    pdesc = PartitionDescriptor.parse(pd_filename)

    assert pdesc.chromosomes == ["foo", "bar"]
    assert pdesc.region_length == 8


def test_parse_yaml_partition_description_effect_types_list(
    tmp_path: pathlib.Path,
) -> None:
    setup_directories(
        tmp_path / "partition_description.yaml",
        textwrap.dedent("""
            coding_bin:
              coding_effect_types:
              - splice-site
              - missense
              - frame-shift
        """),
    )
    pd_filename = tmp_path / "partition_description.yaml"
    pdesc = PartitionDescriptor.parse(pd_filename)

    assert pdesc.coding_effect_types == {
        "splice-site", "missense", "frame-shift",
    }


def test_parse_yaml_partition_description_effect_groups(
    tmp_path: pathlib.Path,
) -> None:
    setup_directories(
        tmp_path / "partition_description.yaml",
        textwrap.dedent("""
            coding_bin:
              coding_effect_types:
              - LGDs
        """),
    )
    pd_filename = tmp_path / "partition_description.yaml"
    pdesc = PartitionDescriptor.parse(pd_filename)

    assert pdesc.coding_effect_types == {
        "frame-shift", "splice-site", "no-frame-shift-newStop", "nonsense",
    }


def test_parse_region_bin_no_region_length(tmp_path: pathlib.Path) -> None:
    setup_directories(
        tmp_path / "partition_description.yaml",
        textwrap.dedent("""
            region_bin:
              chromosomes: foo,bar
        """),
    )
    pd_filename = tmp_path / "partition_description.yaml"
    pdesc = PartitionDescriptor.parse(pd_filename)

    assert pdesc.has_region_bins()
    assert pdesc.chromosomes == ["foo", "bar"]
    assert pdesc.region_length == sys.maxsize


def test_parse_partition_description_no_region_bin(
    tmp_path: pathlib.Path,
) -> None:
    setup_directories(
        tmp_path / "partition_description.yaml",
        textwrap.dedent("""
            family_bin:
              family_bin_size: 2
            frequency_bin:
              rare_boundary: 50
            coding_bin:
              coding_effect_types: splice-site,missense,frame-shift
        """),
    )
    pd_filename = tmp_path / "partition_description.yaml"
    pdesc = PartitionDescriptor.parse(pd_filename)

    assert not pdesc.has_region_bins()
    assert not pdesc.chromosomes
    assert pdesc.region_length == 0

    assert pdesc.family_bin_size == 2
    assert pdesc.rare_boundary == 50


def test_parse_partition_description_no_region_and_family_bin(
    tmp_path: pathlib.Path,
) -> None:
    setup_directories(
        tmp_path / "partition_description.yaml",
        textwrap.dedent("""
            frequency_bin:
              rare_boundary: 50
            coding_bin:
              coding_effect_types: splice-site,missense,frame-shift
        """),
    )
    pd_filename = tmp_path / "partition_description.yaml"
    pdesc = PartitionDescriptor.parse(pd_filename)

    assert not pdesc.has_region_bins()
    assert not pdesc.has_family_bins()

    assert pdesc.has_frequency_bins()
    assert pdesc.rare_boundary == 50

    assert pdesc.has_coding_bins()


def test_partition_directory() -> None:
    assert PartitionDescriptor.partition_directory(
        "work", [("region_bin", "1")]) == "work/region_bin=1"
    assert PartitionDescriptor.partition_directory(
        "s3://work", [("region_bin", "1")]) == "s3://work/region_bin=1"

    assert PartitionDescriptor.partition_directory(
        "work", []) == "work"
    assert PartitionDescriptor.partition_directory(
        "s3://work", []) == "s3://work"

    assert PartitionDescriptor.partition_directory(
        "work", Partition(region_bin="1")) == "work/region_bin=1"
    assert PartitionDescriptor.partition_directory(
        "s3://work", Partition(region_bin="1")) == "s3://work/region_bin=1"

    assert PartitionDescriptor.partition_directory(
        "work", Partition()) == "work"
    assert PartitionDescriptor.partition_directory(
        "s3://work", Partition()) == "s3://work"


@pytest.mark.parametrize("prefix,partition,bucket_index,expected", [
    ("summary", [("region_bin", "1")], 1,
     "summary_region_bin_1_bucket_index_000001.parquet"),
    ("summary", [("region_bin", "1"), ("frequency_bin", "0")], 1,
     "summary_region_bin_1_frequency_bin_0_bucket_index_000001.parquet"),
    ("summary", [("region_bin", "1"), ("frequency_bin", "0"),
                 ("coding_bin", "1")], 0,
     "summary_region_bin_1_frequency_bin_0_coding_bin_1_"
     "bucket_index_000000.parquet"),
    ("merged", [("region_bin", "1")], 1,
     "merged_region_bin_1_bucket_index_000001.parquet"),
    ("merged", [], None,
     "merged.parquet"),
    ("merged", Partition("chr_1"), None,
     "merged_region_bin_chr_1.parquet"),
    ("merged", Partition("chr_1", "0"), None,
     "merged_region_bin_chr_1_frequency_bin_0.parquet"),
    ("merged", Partition("chr_1", "0", "1"), None,
     "merged_region_bin_chr_1_frequency_bin_0_coding_bin_1.parquet"),
    ("merged", Partition("chr_1", "0", "1", "5"), None,
     "merged_region_bin_chr_1_frequency_bin_0_coding_bin_1_"
     "family_bin_5.parquet"),
])
def test_partition_filename(
    prefix: str,
    partition: Partition | list[tuple[str, str]],
    bucket_index: int | None,
    expected: str,
) -> None:
    assert PartitionDescriptor.partition_filename(
        prefix, partition, bucket_index) == \
        expected


def test_partition_descriptor_serialization() -> None:
    pd_content = textwrap.dedent("""
        [region_bin]
        chromosomes = foo,bar
        region_length = 8

        [family_bin]
        family_bin_size = 2

        [frequency_bin]
        rare_boundary = 50

        [coding_bin]
        coding_effect_types = splice-site,missense,frame-shift

    """)
    pdesc1 = PartitionDescriptor.parse_string(pd_content)
    output = pdesc1.serialize()
    pdesc2 = PartitionDescriptor.parse_string(output)

    assert pdesc1.chromosomes == pdesc2.chromosomes
    assert pdesc1.region_length == pdesc2.region_length
    assert pdesc1.family_bin_size == pdesc2.family_bin_size
    assert pdesc1.rare_boundary == pdesc2.rare_boundary
    assert pdesc1.coding_effect_types == pdesc2.coding_effect_types


def test_partition_descriptor_serialization_integer_region_bins() -> None:
    pd_content = textwrap.dedent("""
        [region_bin]
        chromosomes = foo,bar
        region_length = 8
        integer_region_bins = true

        [family_bin]
        family_bin_size = 2

        [frequency_bin]
        rare_boundary = 50

        [coding_bin]
        coding_effect_types = splice-site,missense,frame-shift

    """)
    pdesc1 = PartitionDescriptor.parse_string(pd_content)
    output = pdesc1.serialize()
    pdesc2 = PartitionDescriptor.parse_string(output)

    assert pdesc1.chromosomes == pdesc2.chromosomes
    assert pdesc1.region_length == pdesc2.region_length
    assert pdesc1.integer_region_bins == pdesc2.integer_region_bins
    assert pdesc1.family_bin_size == pdesc2.family_bin_size
    assert pdesc1.rare_boundary == pdesc2.rare_boundary
    assert pdesc1.coding_effect_types == pdesc2.coding_effect_types


def test_empty_partition_descriptor_serialization() -> None:
    pd_content = textwrap.dedent("""
    """)
    pdesc1 = PartitionDescriptor.parse_string(pd_content)
    output = pdesc1.serialize()
    pdesc2 = PartitionDescriptor.parse_string(output)

    assert pdesc1.chromosomes == pdesc2.chromosomes
    assert pdesc1.region_length == pdesc2.region_length
    assert pdesc1.family_bin_size == pdesc2.family_bin_size
    assert pdesc1.rare_boundary == pdesc2.rare_boundary
    assert pdesc1.coding_effect_types == pdesc2.coding_effect_types


def test_partition_descriptor_yaml_serialization() -> None:
    pd_content = textwrap.dedent("""
        region_bin:
            chromosomes: foo,bar
            region_length: 8
        family_bin:
            family_bin_size: 2
        frequency_bin:
            rare_boundary: 50
        coding_bin:
            coding_effect_types: splice-site,missense,frame-shift
    """)

    pdesc1 = PartitionDescriptor.parse_string(pd_content, "yaml")
    output = pdesc1.serialize("yaml")
    pdesc2 = PartitionDescriptor.parse_string(output, "yaml")

    assert pdesc1.chromosomes == pdesc2.chromosomes
    assert pdesc1.region_length == pdesc2.region_length
    assert pdesc1.family_bin_size == pdesc2.family_bin_size
    assert pdesc1.rare_boundary == pdesc2.rare_boundary
    assert pdesc1.coding_effect_types == pdesc2.coding_effect_types


def test_partition_descriptor_yaml_serialization_integer_region_bins() -> None:
    pd_content = textwrap.dedent("""
        region_bin:
            chromosomes: foo,bar
            region_length: 8
            integer_region_bins: true
        family_bin:
            family_bin_size: 2
        frequency_bin:
            rare_boundary: 50
        coding_bin:
            coding_effect_types: splice-site,missense,frame-shift
    """)

    pdesc1 = PartitionDescriptor.parse_string(pd_content, "yaml")
    output = pdesc1.serialize("yaml")
    pdesc2 = PartitionDescriptor.parse_string(output, "yaml")

    assert pdesc1.chromosomes == pdesc2.chromosomes
    assert pdesc1.region_length == pdesc2.region_length
    assert pdesc1.integer_region_bins == pdesc2.integer_region_bins
    assert pdesc1.family_bin_size == pdesc2.family_bin_size
    assert pdesc1.rare_boundary == pdesc2.rare_boundary
    assert pdesc1.coding_effect_types == pdesc2.coding_effect_types


def test_empty_partition_descriptor_yaml_serialization() -> None:
    pd_content = textwrap.dedent("""
    """)
    pdesc1 = PartitionDescriptor.parse_string(pd_content, "yaml")
    output = pdesc1.serialize("yaml")
    pdesc2 = PartitionDescriptor.parse_string(output, "yaml")

    assert pdesc1.chromosomes == pdesc2.chromosomes
    assert pdesc1.region_length == pdesc2.region_length
    assert pdesc1.family_bin_size == pdesc2.family_bin_size
    assert pdesc1.rare_boundary == pdesc2.rare_boundary
    assert pdesc1.coding_effect_types == pdesc2.coding_effect_types


def test_partition_descriptor_varint_dirs_simple() -> None:
    pd_content = textwrap.dedent("""
        region_bin:
            chromosomes: foo,bar
            region_length: 8
    """)

    part_desc = PartitionDescriptor.parse_string(pd_content, "yaml")
    sum_parts, fam_parts = part_desc.get_variant_partitions(
        {"foo": 16, "bar": 4},
    )
    assert len(sum_parts) == 3
    assert len(fam_parts) == 3

    assert sum_parts[0] == [("region_bin", "foo_0")]
    assert sum_parts[1] == [("region_bin", "foo_1")]
    assert sum_parts[2] == [("region_bin", "bar_0")]


def test_partition_descriptor_varint_dirs_simple_integer_bins() -> None:
    pd_content = textwrap.dedent("""
        region_bin:
            chromosomes: foo,bar
            region_length: 8
            integer_region_bins: true
    """)

    part_desc = PartitionDescriptor.parse_string(pd_content, "yaml")
    sum_parts, fam_parts = part_desc.get_variant_partitions(
        {"foo": 16, "bar": 4},
    )
    assert len(sum_parts) == 3
    assert len(fam_parts) == 3

    assert sum_parts[0] == [("region_bin", "0")]
    assert sum_parts[1] == [("region_bin", "1")]
    assert sum_parts[2] == [("region_bin", "10000")]


def test_partition_descriptor_varint_dirs_full() -> None:
    family_bin_size = 2
    pd_content = textwrap.dedent(f"""
        region_bin:
            chromosomes: foo,bar
            region_length: 8
        family_bin:
            family_bin_size: {family_bin_size}
        frequency_bin:
            rare_boundary: 50
        coding_bin:
            coding_effect_types: splice-site,missense,frame-shift
    """)

    part_desc = PartitionDescriptor.parse_string(pd_content, "yaml")
    sum_parts, fam_parts = part_desc.get_variant_partitions(
        {"foo": 16, "bar": 4, "barz": 10},
    )
    # num region bins * num freq_bins * num coding_bins
    assert len(sum_parts) == 5 * 4 * 2
    assert len(fam_parts) == 2 * len(sum_parts)

    assert sum_parts[0] == [
        ("region_bin", "foo_0"), ("frequency_bin", "0"), ("coding_bin", "0"),
    ]
    assert sum_parts[1] == [
        ("region_bin", "foo_0"), ("frequency_bin", "0"), ("coding_bin", "1"),
    ]
    assert sum_parts[2] == [
        ("region_bin", "foo_0"), ("frequency_bin", "1"), ("coding_bin", "0"),
    ]
    assert sum_parts[-1] == [
        ("region_bin", "other_1"), ("frequency_bin", "3"), ("coding_bin", "1"),
    ]

    for i, fam_part in enumerate(fam_parts):
        sum_part = sum_parts[i // family_bin_size]
        assert fam_part[:-1] == sum_part
        assert fam_part[-1] == ("family_bin", str(i % family_bin_size))


def test_partition_descriptor_varint_dirs_full_integer_bins() -> None:
    family_bin_size = 2
    pd_content = textwrap.dedent(f"""
        region_bin:
            chromosomes: foo,bar
            region_length: 8
            integer_region_bins: true
        family_bin:
            family_bin_size: {family_bin_size}
        frequency_bin:
            rare_boundary: 50
        coding_bin:
            coding_effect_types: splice-site,missense,frame-shift
    """)

    part_desc = PartitionDescriptor.parse_string(pd_content, "yaml")
    sum_parts, fam_parts = part_desc.get_variant_partitions(
        {"foo": 16, "bar": 4, "barz": 10},
    )

    # num region bins * num freq_bins * num coding_bins
    assert len(sum_parts) == 5 * 4 * 2
    assert len(fam_parts) == 2 * len(sum_parts)

    assert sum_parts[0] == [
        ("region_bin", "0"), ("frequency_bin", "0"), ("coding_bin", "0"),
    ]
    assert sum_parts[1] == [
        ("region_bin", "0"), ("frequency_bin", "0"), ("coding_bin", "1"),
    ]
    assert sum_parts[2] == [
        ("region_bin", "0"), ("frequency_bin", "1"), ("coding_bin", "0"),
    ]
    assert sum_parts[16] == [
        ("region_bin", "10000"), ("frequency_bin", "0"), ("coding_bin", "0"),
    ]
    assert sum_parts[-1] == [
        ("region_bin", "10000001"), ("frequency_bin", "3"),
        ("coding_bin", "1"),
    ]

    for i, fam_part in enumerate(fam_parts):
        sum_part = sum_parts[i // family_bin_size]
        assert fam_part[:-1] == sum_part
        assert fam_part[-1] == ("family_bin", str(i % family_bin_size))


@pytest.mark.parametrize("region, region_bins", [
    (Region("foo", 1, 7), ["foo_0"]),
    (Region("foo", 1, 8), ["foo_0"]),
    (Region("foo", 1), ["foo_0", "foo_1", "foo_2"]),
    (Region("foo", stop=8), ["foo_0"]),
    (Region("foo", stop=16), ["foo_0", "foo_1"]),
    (Region("foo", stop=17), ["foo_0", "foo_1", "foo_2"]),
    (Region("foo"), ["foo_0", "foo_1", "foo_2"]),
    (Region("foo", 1, 24), ["foo_0", "foo_1", "foo_2"]),
    (Region("foo", 1, 999_999_999), ["foo_0", "foo_1", "foo_2"]),
])
def test_region_to_region_bins(
    region: Region,
    region_bins: list[str],
) -> None:
    pd = PartitionDescriptor.parse_string("""
        [region_bin]
        chromosomes = foo
        region_length = 8
    """)
    chrom_lens = {"foo": 24}

    assert pd.region_to_region_bins(region, chrom_lens) == region_bins


@pytest.mark.parametrize("region, region_bins", [
    (Region("foo", 1, 7), ["0"]),
    (Region("foo", 1, 8), ["0"]),
    (Region("foo", 1), ["0", "1", "2"]),
    (Region("foo", stop=8), ["0"]),
    (Region("foo", stop=16), ["0", "1"]),
    (Region("foo", stop=17), ["0", "1", "2"]),
    (Region("foo"), ["0", "1", "2"]),
    (Region("foo", 1, 24), ["0", "1", "2"]),
    (Region("foo", 1, 999_999_999), ["0", "1", "2"]),
    (Region("baz"), ["10000000", "10000001"]),
    (Region("bar"), ["10000000", "10000001", "10000002"]),
])
def test_region_to_region_bins_integer_bins(
    region: Region,
    region_bins: list[str],
) -> None:
    pd = PartitionDescriptor.parse_string("""
        [region_bin]
        chromosomes = foo
        region_length = 8
        integer_region_bins = true
    """)
    chrom_lens = {"foo": 24, "bar": 17, "baz": 12}

    assert pd.region_to_region_bins(region, chrom_lens) == region_bins


def test_path_to_partitions() -> None:
    res = PartitionDescriptor.path_to_partitions(
        "region_bin=foo_0/frequency_bin=1/coding_bin=0",
    )
    assert res == [("region_bin", "foo_0"), ("frequency_bin", "1"),
                   ("coding_bin", "0")]

    res = PartitionDescriptor.path_to_partitions(
        "region_bin=foo_1/frequency_bin=2/coding_bin=1/variants.parquet",
    )
    assert res == [("region_bin", "foo_1"), ("frequency_bin", "2"),
                   ("coding_bin", "1")]


@pytest.mark.parametrize("chroms, expected", [
    (["foo"], {
        "foo_0": [Region("foo", 1, 8)],
        "foo_1": [Region("foo", 9, 16)],
        "foo_2": [Region("foo", 17, 24)],
     }),
    (["bar"], {
        "other_0": [Region("bar", 1, 8)],
        "other_1": [Region("bar", 9, 16)],
        "other_2": [Region("bar", 17, 17)],
    }),
    (["baz"], {
        "other_0": [Region("baz", 1, 8)],
        "other_1": [Region("baz", 9, 12)],
    }),
    (["bar", "baz"], {
        "other_0": [Region("bar", 1, 8), Region("baz", 1, 8)],
        "other_1": [Region("bar", 9, 16), Region("baz", 9, 12)],
        "other_2": [Region("bar", 17, 17)],
    }),
    (["foo", "bar", "baz"], {
        "foo_0": [Region("foo", 1, 8)],
        "foo_1": [Region("foo", 9, 16)],
        "foo_2": [Region("foo", 17, 24)],
        "other_0": [Region("bar", 1, 8), Region("baz", 1, 8)],
        "other_1": [Region("bar", 9, 16), Region("baz", 9, 12)],
        "other_2": [Region("bar", 17, 17)],
    }),
])
def test_make_region_bins_regions(
    chroms: list[str],
    expected: dict[str, list[Region]],
) -> None:
    pd = PartitionDescriptor.parse_string("""
        [region_bin]
        chromosomes = foo
        region_length = 8
    """)
    chrom_lens = {
        "foo": 24,
        "bar": 17,
        "baz": 12,
    }
    result = pd.make_region_bins_regions(
        chroms, chrom_lens)
    assert result == expected


@pytest.mark.parametrize("chroms, expected", [
    (["foo"], {
        "0": [Region("foo", 1, 8)],
        "1": [Region("foo", 9, 16)],
        "2": [Region("foo", 17, 24)],
     }),
    (["bar"], {
        "10000000": [Region("bar", 1, 8)],
        "10000001": [Region("bar", 9, 16)],
        "10000002": [Region("bar", 17, 17)],
    }),
    (["baz"], {
        "10000000": [Region("baz", 1, 8)],
        "10000001": [Region("baz", 9, 12)],
    }),
    (["bar", "baz"], {
        "10000000": [Region("bar", 1, 8), Region("baz", 1, 8)],
        "10000001": [Region("bar", 9, 16), Region("baz", 9, 12)],
        "10000002": [Region("bar", 17, 17)],
    }),
    (["foo", "bar", "baz"], {
        "0": [Region("foo", 1, 8)],
        "1": [Region("foo", 9, 16)],
        "2": [Region("foo", 17, 24)],
        "10000000": [Region("bar", 1, 8), Region("baz", 1, 8)],
        "10000001": [Region("bar", 9, 16), Region("baz", 9, 12)],
        "10000002": [Region("bar", 17, 17)],
    }),
])
def test_make_region_bins_regions_integer_bins(
    chroms: list[str],
    expected: dict[str, list[Region]],
) -> None:
    pd = PartitionDescriptor.parse_string("""
        [region_bin]
        chromosomes = foo
        region_length = 8
        integer_region_bins = true
    """)
    chrom_lens = {
        "foo": 24,
        "bar": 17,
        "baz": 12,
    }
    result = pd.make_region_bins_regions(
        chroms, chrom_lens)
    assert result == expected


@pytest.mark.parametrize("chrom_lens, expected", [
    ({"foo": 24, "bar": 15},
     ["foo_0", "foo_1", "foo_2", "other_0", "other_1"]),
    ({"foo": 25, "bar": 15},
     ["foo_0", "foo_1", "foo_2", "foo_3", "other_0", "other_1"]),
    ({"foo": 16, "bar": 8, "baz": 12},
     ["foo_0", "foo_1", "other_0", "other_1"]),
])
def test_make_all_region_bins(
    chrom_lens: dict[str, int],
    expected: list[str],
) -> None:
    pd = PartitionDescriptor.parse_string("""
        [region_bin]
        chromosomes = foo
        region_length = 8
    """)

    result = pd.make_all_region_bins(chrom_lens)
    assert result == expected


@pytest.mark.parametrize("chrom_lens, expected", [
    ({"foo": 24, "bar": 15},
     ["0", "1", "2", "10000000", "10000001"]),
    ({"foo": 25, "bar": 15},
     ["0", "1", "2", "3", "10000000", "10000001"]),
    ({"foo": 16, "bar": 8, "baz": 12},
     ["0", "1", "10000000", "10000001"]),
])
def test_make_all_region_bins_integer_bins(
    chrom_lens: dict[str, int],
    expected: list[str],
) -> None:
    pd = PartitionDescriptor.parse_string("""
        [region_bin]
        chromosomes = foo
        region_length = 8
        integer_region_bins = true
    """)

    result = pd.make_all_region_bins(chrom_lens)
    assert result == expected


@pytest.mark.parametrize("region, region_bins", [
    (Region("chr1", 100, 205), ["chr1_0", "chr1_1", "chr1_2"]),
])
def test_region_to_region_bins_additional(
    region: Region,
    region_bins: list[str],
) -> None:
    pd = PartitionDescriptor.parse_string("""
        [region_bin]
        chromosomes = chr1
        region_length = 100
    """)
    chrom_lens = {"chr1": 300}

    assert pd.region_to_region_bins(region, chrom_lens) == region_bins


@pytest.mark.parametrize("chrom_lens, expected", [
    ({"chr1": 100, "chr2": 50},
     [Partition("chr1_0"), Partition("chr2_0")]),
    ({"chr1": 100, "chr2": 50, "chr3": 20},
     [Partition("chr1_0"), Partition("chr2_0"), Partition("other_0")]),
    ({"chr1": 150, "chr2": 50},
     [Partition("chr1_0"), Partition("chr1_1"), Partition("chr2_0")]),
])
def test_build_summary_partitions_region_bins(
    chrom_lens: dict[str, int],
    expected: list[Partition],
) -> None:
    pd = PartitionDescriptor.parse_string("""
        [region_bin]
        chromosomes = chr1,chr2
        region_length = 100
    """)

    result = pd.build_summary_partitions(chrom_lens)
    assert result == expected


@pytest.mark.parametrize("region_length, count, region_bins", [
    (200, 2, ["chr1_0", "chr2_0"]),
    (100, 3, ["chr1_0", "chr1_1", "chr2_0"]),
    (70, 4, ["chr1_0", "chr1_1", "chr1_2", "chr2_0"]),
    (50, 5, ["chr1_0", "chr1_1", "chr1_2", "chr1_3", "chr2_0"]),
])
def test_build_summary_partitions_group_by_region_bin(
    region_length: int,
    count: int,
    region_bins: list[str],
) -> None:
    chrom_lens = {"chr1": 200, "chr2": 50}
    pd = PartitionDescriptor.parse_string(f"""
        [region_bin]
        chromosomes = chr1,chr2
        region_length = {region_length}
    """)
    result = list(itertools.groupby(
        pd.build_summary_partitions(chrom_lens),
        key=operator.attrgetter("region_bin"),
    ))
    assert len(result) == count
    assert [rb for rb, _ in result] == region_bins


def test_build_summary_partitions_group_by_region_bin_without_region_bins(
) -> None:
    chrom_lens = {"chr1": 200, "chr2": 50}
    pd = PartitionDescriptor.parse_string("""
        [frequency_bin]
        rare_boundary = 50
    """)
    result = list(itertools.groupby(
        pd.build_summary_partitions(chrom_lens),
        key=operator.attrgetter("region_bin"),
    ))
    assert len(result) == 1


@pytest.mark.parametrize("chrom_lens, expected", [
    ({"chr1": 100},
     [Partition("chr1_0", "0"), Partition("chr1_0", "1"),
      Partition("chr1_0", "2"), Partition("chr1_0", "3")]),
    ({"chr1": 150},
     [Partition("chr1_0", "0"), Partition("chr1_0", "1"),
      Partition("chr1_0", "2"), Partition("chr1_0", "3"),
      Partition("chr1_1", "0"), Partition("chr1_1", "1"),
      Partition("chr1_1", "2"), Partition("chr1_1", "3")]),
])
def test_build_summary_partitions_region_and_frequency_bins(
    chrom_lens: dict[str, int],
    expected: list[Partition],
) -> None:
    pd = PartitionDescriptor.parse_string("""
        [region_bin]
        chromosomes = chr1,chr2
        region_length = 100

        [frequency_bin]
        rare_boundary = 50

    """)

    result = pd.build_summary_partitions(chrom_lens)
    assert result == expected


@pytest.mark.parametrize("chrom_lens, expected", [
    ({"chr1": 100},
     [Partition("chr1_0", coding_bin="0"),
      Partition("chr1_0", coding_bin="1")]),
    ({"chr1": 150},
     [Partition("chr1_0", coding_bin="0"),
      Partition("chr1_0", coding_bin="1"),
      Partition("chr1_1", coding_bin="0"),
      Partition("chr1_1", coding_bin="1")]),
])
def test_build_summary_partitions_region_and_coding_bins(
    chrom_lens: dict[str, int],
    expected: list[Partition],
) -> None:
    pd = PartitionDescriptor.parse_string("""
        [region_bin]
        chromosomes = chr1,chr2
        region_length = 100

        [coding_bin]
        coding_effect_types = missense,splice-site,frame-shift
    """)

    result = pd.build_summary_partitions(chrom_lens)
    assert result == expected


@pytest.mark.parametrize("chrom_lens, expected", [
    ({"chr1": 100},
     [Partition("chr1_0", coding_bin="0"),
      Partition("chr1_0", coding_bin="1")]),
    ({"chr1": 150},
     [Partition("chr1_0", coding_bin="0"),
      Partition("chr1_0", coding_bin="1"),
      Partition("chr1_1", coding_bin="0"),
      Partition("chr1_1", coding_bin="1")]),
])
def test_build_summary_partitions_region_and_coding_and_family_bins(
    chrom_lens: dict[str, int],
    expected: list[Partition],
) -> None:
    pd = PartitionDescriptor.parse_string("""
        [region_bin]
        chromosomes = chr1,chr2
        region_length = 100

        [coding_bin]
        coding_effect_types = missense,splice-site,frame-shift

        [family_bin]
        family_bin_size = 2

    """)

    result = pd.build_summary_partitions(chrom_lens)
    assert result == expected


@pytest.mark.parametrize("chrom_lens, expected", [
    ({"chr1": 100},
     [Partition("chr1_0", coding_bin="0"),
      Partition("chr1_0", coding_bin="1")]),
    ({"chr1": 150},
     [Partition("chr1_0", coding_bin="0"),
      Partition("chr1_0", coding_bin="1"),
      Partition("chr1_1", coding_bin="0"),
      Partition("chr1_1", coding_bin="1")]),
])
def test_build_family_partitions_region_and_coding_bins(
    chrom_lens: dict[str, int],
    expected: list[Partition],
) -> None:
    pd = PartitionDescriptor.parse_string("""
        [region_bin]
        chromosomes = chr1,chr2
        region_length = 100

        [coding_bin]
        coding_effect_types = missense,splice-site,frame-shift

    """)

    result = pd.build_family_partitions(chrom_lens)
    assert result == expected


@pytest.mark.parametrize("chrom_lens, expected", [
    ({"chr1": 100},
     [Partition("chr1_0", coding_bin="0", family_bin="0"),
      Partition("chr1_0", coding_bin="0", family_bin="1"),
      Partition("chr1_0", coding_bin="1", family_bin="0"),
      Partition("chr1_0", coding_bin="1", family_bin="1")]),
    ({"chr1": 150},
     [Partition("chr1_0", coding_bin="0", family_bin="0"),
      Partition("chr1_0", coding_bin="0", family_bin="1"),
      Partition("chr1_0", coding_bin="1", family_bin="0"),
      Partition("chr1_0", coding_bin="1", family_bin="1"),
      Partition("chr1_1", coding_bin="0", family_bin="0"),
      Partition("chr1_1", coding_bin="0", family_bin="1"),
      Partition("chr1_1", coding_bin="1", family_bin="0"),
      Partition("chr1_1", coding_bin="1", family_bin="1")]),
])
def test_build_family_partitions_region_and_coding_and_family_bins(
    chrom_lens: dict[str, int],
    expected: list[Partition],
) -> None:
    pd = PartitionDescriptor.parse_string("""
        [region_bin]
        chromosomes = chr1,chr2
        region_length = 100

        [coding_bin]
        coding_effect_types = missense,splice-site,frame-shift

        [family_bin]
        family_bin_size = 2
    """)

    result = pd.build_family_partitions(chrom_lens)
    assert result == expected


def test_partition_equality() -> None:
    p1 = Partition(region_bin="foo_0", frequency_bin="1", coding_bin="0")
    p2 = Partition(region_bin="foo_0", frequency_bin="1", coding_bin="0")
    p3 = Partition(region_bin="foo_1", frequency_bin="1", coding_bin="0")
    p4 = Partition(
        region_bin="foo_1", coding_bin="0", family_bin="1")
    p5 = Partition(
        region_bin="foo_1", coding_bin="0", family_bin="1")
    p6 = Partition(
        region_bin="foo_1", coding_bin="0", family_bin="0")

    assert p1 == p2
    assert p1 != p3
    assert p2 != p3

    assert hash(p1) == hash(p2)
    assert hash(p1) != hash(p3)
    assert hash(p2) != hash(p3)

    assert p4 == p5
    assert p4 != p6


def test_empty_partition_descritor() -> None:
    pd = PartitionDescriptor()
    assert not pd.has_region_bins()
    assert not pd.has_frequency_bins()
    assert not pd.has_coding_bins()
    assert not pd.has_family_bins()

    assert pd.chromosomes == []
    assert pd.region_length == 0
    assert pd.integer_region_bins is False
    assert pd.family_bin_size == 0
    assert pd.rare_boundary == 0
    assert pd.coding_effect_types == set()

    content = pd.serialize("yaml")
    assert content == ""


def test_empty_partition_descritor_summary_partitions() -> None:
    pd = PartitionDescriptor()

    summary_partitions = pd.build_summary_partitions({"chr1": 100, "chr2": 50})
    assert summary_partitions == [Partition()]


def test_empty_partition_descritor_family_partitions() -> None:
    pd = PartitionDescriptor()

    family_partitions = pd.build_family_partitions({"chr1": 100, "chr2": 50})
    assert family_partitions == [Partition()]


def test_empty_partition_filename() -> None:
    pd = PartitionDescriptor()

    filename = pd.partition_filename("summary", [], 1)
    assert filename == "summary_bucket_index_000001.parquet"

    filename = pd.partition_filename("summary", Partition(), 1)
    assert filename == "summary_bucket_index_000001.parquet"

    filename = pd.partition_filename("merged", [], None)
    assert filename == "merged.parquet"

    filename = pd.partition_filename("merged", Partition(), None)
    assert filename == "merged.parquet"
