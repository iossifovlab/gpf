# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import sys
import textwrap

import pytest

from dae.parquet.partition_descriptor import PartitionDescriptor
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


def test_partition_filename() -> None:
    assert PartitionDescriptor.partition_filename(
        "summary", [("region_bin", "1")], 1) == \
        "summary_region_bin_1_bucket_index_000001.parquet"


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
        ("region_bin", "10000001"), ("frequency_bin", "3"), ("coding_bin", "1"),
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
