# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap

import pysam
import pytest
from dae.genomic_resources.testing import setup_tabix
from dae.utils.regions import (
    BedRegion,
    Region,
    collapse,
    collapse_no_chrom,
    get_chromosome_length_tabix,
    split_into_regions,
)


@pytest.mark.parametrize(
    "region,expected",
    [
        ("1:1-2", Region("1", 1, 2)),
        ("chr1:1-2", Region("chr1", 1, 2)),
        ("X:1-2", Region("X", 1, 2)),
        ("chrX:1-2", Region("chrX", 1, 2)),
        ("GL000192.1:1-2", Region("GL000192.1", 1, 2)),
        ("chrUn_GL000218v1:1-2", Region("chrUn_GL000218v1", 1, 2)),
        ("chr4_KI270790v1_alt:1-2", Region("chr4_KI270790v1_alt", 1, 2)),
        ("chr1:1", Region("chr1", 1, 1)),
        ("chr1:1,000,000-2,000,000", Region("chr1", 1_000_000, 2_000_000)),
        ("chr1_KI270706v1_random", Region("chr1_KI270706v1_random")),
        ("HLA-A*01:01:01:01:1-2", Region("HLA-A*01:01:01:01", 1, 2)),
    ],
)
def test_parse_regions(region: str, expected: Region) -> None:
    result = Region.from_str(region)
    # assert result is not None
    assert result == expected


@pytest.mark.parametrize(
    "data,expected",
    [
        ("1:1-2,1:1-3", [Region("1", 1, 3)]),
        ("1:1-2,1:2-3", [Region("1", 1, 3)]),
        ("1:1-2,2:2-3", [Region("1", 1, 2), Region("2", 2, 3)]),
        ("1:1-2,1:3-4", [Region("1", 1, 2), Region("1", 3, 4)]),
    ],
)
def test_collapse_simple(data: str, expected: list[Region]) -> None:
    regions = [Region.from_str(r) for r in data.split(",")]
    result = collapse(regions)

    assert len(result) == len(expected)
    for res, exp in zip(result, expected, strict=True):
        assert res == exp


@pytest.mark.parametrize(
    "data,expected",
    [
        ("1:1-2,1:1-3", [Region("1", 1, 3)]),
        ("1:1-2,1:2-3", [Region("1", 1, 3)]),
        ("1:1-2,1:3-4", [Region("1", 1, 2), Region("1", 3, 4)]),
    ],
)
def test_collapse_no_chrom_simple(data: str, expected: list[Region]) -> None:
    regions = [BedRegion.from_str(r) for r in data.split(",")]
    result = collapse_no_chrom(regions)

    assert len(result) == len(expected)
    for res, exp in zip(result, expected, strict=True):
        assert res == exp


@pytest.mark.parametrize(
    "chrom,chrom_length,region_size,expected",
    [
        ("1", 10, 5, [Region("1", 1, 5), Region("1", 6, 10)]),
        ("1", 10, 100, [Region("1", 1, 10)]),
        ("1", 4, 1, [
            Region("1", 1, 1),
            Region("1", 2, 2),
            Region("1", 3, 3),
            Region("1", 4, 4),
        ]),
    ],
)
def test_split_into_regions(
    chrom: str, chrom_length: int, region_size: int,
    expected: list[Region],
) -> None:
    result = split_into_regions(chrom, chrom_length, region_size)

    assert len(result) == len(expected)

    for i, res in enumerate(result):
        assert res == expected[i], f"{res} != {expected[i]}"


def test_split_into_regions_with_start_pos() -> None:
    expected = [
        Region("1", 21, 30),
        Region("1", 31, 40),
        Region("1", 41, 50),
    ]
    result = split_into_regions("1", 50, 10, start=21)
    assert len(result) == len(expected)
    for i, res in enumerate(result):
        assert res == expected[i], f"{res} != {expected[i]}"

    expected = [
        Region("1", 1, 10),
        Region("1", 11, 20),
        Region("1", 21, 30),
        Region("1", 31, 40),
        Region("1", 41, 50),
    ]
    result = split_into_regions("1", 50, 10, start=10)
    assert len(result) == len(expected)
    for i, res in enumerate(result):
        assert res == expected[i], f"{res} != {expected[i]}"


def test_split_into_regions_zero_region_length() -> None:
    assert split_into_regions("1", 50, 0) == [Region("1")]


@pytest.fixture
def sample_tabix(tmp_path: pathlib.Path) -> pysam.TabixFile:
    filepath = tmp_path / "data.txt.gz"
    setup_tabix(
        filepath,
        """
            #chrom pos_begin pos_end
            1     10        12
            1     11        11
            1     12        13
            1     13        14
            2     1         2
            2     1         4
            3     500000    500010
        """, seq_col=0, start_col=1, end_col=2,
    )
    return pysam.TabixFile(str(filepath))


@pytest.mark.parametrize(
    "precision",
    [
        5_000_000,
        1000,
        100,
        1,
    ],
)
def test_get_chrom_length(
    sample_tabix: pysam.TabixFile, precision: int,
) -> None:
    one_length = get_chromosome_length_tabix(
        sample_tabix, "1", precision=precision)
    assert one_length is not None
    assert one_length > 14
    assert one_length - 14 <= precision

    two_length = get_chromosome_length_tabix(
        sample_tabix, "2", precision=precision)
    assert two_length is not None

    assert two_length > 4
    assert two_length - 14 <= precision

    three_length = get_chromosome_length_tabix(
        sample_tabix, "3", precision=precision,
    )
    assert three_length is not None
    assert three_length > 500_010
    assert three_length - 500_010 <= precision


@pytest.mark.parametrize(
    "reg1,reg2,expected",
    [
        (Region("1", 1, 10), Region("1", 2, 9), True),
        (Region("1", 1, 10), Region("1", 1, 10), True),
        (Region("1", 2, 10), Region("1", 1, 10), False),
        (Region("1", 1, 11), Region("1", 1, 10), True),
        (Region("1", 1), Region("1", 1, 10), True),
        (Region("1", 1), Region("1", 1), True),
        (Region("1", 2), Region("1", 1), False),
        (Region("1", 2), Region("1"), False),
        (Region("1"), Region("1"), True),
        (Region("1"), Region("1", 1), True),
        (Region("1"), Region("1", 1, 10), True),
        (Region("1", None, 10), Region("1", 1, 10), True),
        (Region("1", None, 10), Region("1", None, 10), True),
        (Region("1", None, 10), Region("1"), False),
        (Region("1", None, 10), Region("1", 1), False),
    ],
)
def test_region_contains(
    reg1: Region,
    reg2: Region,
    expected: bool,  # noqa: FBT001
) -> None:
    assert reg1.contains(reg2) == expected


@pytest.mark.parametrize(
    "reg1,reg2,expected",
    [
        # None variations, overlapping
        (Region("1", None, None), Region("1", None, None), True),
        (Region("1", None, None), Region("1", 1, None), True),
        (Region("1", None, None), Region("1", None, 10), True),
        (Region("1", None, None), Region("1", 1, 10), True),
        (Region("1", 1, None), Region("1", 1, None), True),
        (Region("1", 1, None), Region("1", None, 10), True),
        (Region("1", 1, None), Region("1", 1, 10), True),
        (Region("1", 1, None), Region("1", 1, 1), True),
        (Region("1", None, 10), Region("1", None, 10), True),
        (Region("1", None, 10), Region("1", 1, 10), True),
        (Region("1", None, 10), Region("1", 10, 20), True),
        # None variations, non-overlapping
        (Region("1", None, 10), Region("1", 11, 20), False),
        (Region("1", 10, 20), Region("1", 21, None), False),
        # Same region
        (Region("1", 1, 10), Region("1", 1, 10), True),
        # Subregion
        (Region("1", 1, 20), Region("1", 5, 10), True),
        # Partial overlap, left side
        (Region("1", 1, 5), Region("1", 1, 10), True),
        (Region("1", 1, 1), Region("1", 1, 10), True),  # single base
        # Partial overlap, right side
        (Region("1", 5, 10), Region("1", 1, 10), True),
        (Region("1", 10, 10), Region("1", 1, 10), True),  # single base
        # No overlap, left side
        (Region("1", 1, 5), Region("1", 6, 10), False),
        # No overlap, right side
        (Region("1", 6, 10), Region("1", 1, 5), False),
    ],
)
def test_region_intersects(
    reg1: Region, reg2: Region, expected: Region,
) -> None:
    assert reg1.intersects(reg2) == expected


@pytest.mark.parametrize(
    "reg1,reg2,expected",
    [
        (Region("1", 1, 10), Region("1", 2, 9), Region("1", 2, 9)),
        (Region("1", 1, 10), Region("1", 1, 10), Region("1", 1, 10)),
        (Region("1", 2, 10), Region("1", 1, 10), Region("1", 2, 10)),
        (Region("1", 1, 11), Region("1", 1, 10), Region("1", 1, 10)),
        (Region("1", 1), Region("1", 1, 10), Region("1", 1, 10)),
        (Region("1", 1), Region("1", 1), Region("1", 1)),
        (Region("1", 2), Region("1", 1), Region("1", 2)),
        (Region("1", 2), Region("1"), Region("1", 2)),
        (Region("1"), Region("1"), Region("1")),
        (Region("1"), Region("1", 1), Region("1", 1)),
        (Region("1"), Region("1", 1, 10), Region("1", 1, 10)),
        (Region("1", None, 10), Region("1", 1, 10), Region("1", 1, 10)),
        (Region("1", None, 10), Region("1", None, 10), Region("1", None, 10)),
        (Region("1", None, 10), Region("1"), Region("1", None, 10)),
        (Region("1", None, 10), Region("1", 1), Region("1", 1, 10)),
    ],
)
def test_region_intersection(
    reg1: Region, reg2: Region, expected: Region,
) -> None:
    assert reg1.intersection(reg2) == expected


def test_get_chromosome_length_tabix_avoid_infinite_loop(
    tmp_path: pathlib.Path,
) -> None:
    """
    If the tabix file is malformed and cannot provide any records,
    the function should not enter an infinite loop.
    """

    in_content = textwrap.dedent("""
        dummyCol1 chrom   dummyCol2 pos  dummyCol3
        ?         chr1    ?         23   ?
    """)
    in_file = tmp_path / "in.txt.gz"
    # in this case, the tabix file will be malformed
    # since the header does not start with a '#' symbol,
    # and the line has not been skipped in setup_tabix.
    setup_tabix(in_file, in_content,
                seq_col=1, start_col=3, end_col=3, line_skip=0)

    assert get_chromosome_length_tabix(
        pysam.TabixFile(str(in_file)), "chr1") is None
