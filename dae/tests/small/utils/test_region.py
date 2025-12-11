# pylint: disable=W0621,C0114,C0116,C0117,W0212,W0613,C0121

import pathlib
import textwrap

import pysam
import pytest
from dae.genomic_resources.testing import (
    setup_tabix,
    setup_vcf,
)
from dae.utils.regions import (
    BedRegion,
    Region,
    _diff,
    all_regions_from_chrom,
    bedfile2regions,
    calc_bin_begin,
    calc_bin_end,
    calc_bin_index,
    coalesce,
    collapse,
    collapse_no_chrom,
    connected_component,
    difference,
    get_chromosome_length_tabix,
    intersection,
    regions2bedfile,
    split_into_regions,
    total_length,
    union,
    unique_regions,
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
        ("1", 10, 10, [Region("1", 1, 10)]),
        ("1", 10, 11, [Region("1", 1, 10)]),
        ("1", 11, 10, [Region("1", 1, 10), Region("1", 11, 20)]),
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


@pytest.fixture
def sample_vcf(tmp_path: pathlib.Path) -> pathlib.Path:
    root_path = tmp_path / "vcf_score"
    return setup_vcf(
        root_path / "score.vcf.gz", """
##fileformat=VCFv4.0
##contig=<ID=1>
##contig=<ID=2>
##contig=<ID=3>
#CHROM POS      ID  REF ALT    QUAL FILTER  INFO
1      29999977 .   A   G      .    .       .
1      29999993 .   T   C      .    .       .
1      29999999 .   T   TAAAAA .    .       .
""")


@pytest.mark.parametrize(
    "precision",
    [
        5_000_000,
        1000,
        100,
        1,
    ],
)
def test_get_chrom_length_vcf(
    sample_vcf: pathlib.Path,
    precision: int,
) -> None:
    variant_file = pysam.VariantFile(str(sample_vcf))
    one_length = get_chromosome_length_tabix(
        variant_file, "1", precision=precision)
    assert one_length is not None
    assert one_length >= 30_000_000
    assert abs(one_length - 30_000_000) <= precision


# Additional tests for better coverage

def test_coalesce() -> None:
    assert coalesce(5, 10) == 5
    assert coalesce(None, 10) == 10
    assert coalesce(0, 10) == 0


def test_bedfile2regions_and_regions2bedfile(tmp_path: pathlib.Path) -> None:
    bed_file = tmp_path / "test.bed"
    bed_file.write_text("chr1\t0\t100\nchr2\t50\t150\n")

    regions = bedfile2regions(str(bed_file))
    assert len(regions) == 2
    assert regions[0].chrom == "chr1"
    assert regions[0].start == 1
    assert regions[0].stop == 100
    assert regions[1].chrom == "chr2"
    assert regions[1].start == 51
    assert regions[1].stop == 150

    # Test writing back
    output_bed = tmp_path / "output.bed"
    regions2bedfile(regions, str(output_bed))
    content = output_bed.read_text()
    assert "chr1\t0\t100\n" in content
    assert "chr2\t50\t150\n" in content


def test_bedfile2regions_with_comments(tmp_path: pathlib.Path) -> None:
    bed_file = tmp_path / "test.bed"
    bed_file.write_text("# Comment line\nchr1\t0\t100\n")

    regions = bedfile2regions(str(bed_file))
    assert len(regions) == 1
    assert regions[0].chrom == "chr1"


@pytest.mark.parametrize(
    "bin_len,bin_idx,expected_begin",
    [
        (10, 0, 1),
        (10, 1, 11),
        (10, 2, 21),
        (100, 0, 1),
        (100, 5, 501),
    ],
)
def test_calc_bin_begin(
    bin_len: int, bin_idx: int, expected_begin: int,
) -> None:
    assert calc_bin_begin(bin_len, bin_idx) == expected_begin


@pytest.mark.parametrize(
    "bin_len,bin_idx,expected_end",
    [
        (10, 0, 10),
        (10, 1, 20),
        (10, 2, 30),
        (100, 0, 100),
        (100, 5, 600),
    ],
)
def test_calc_bin_end(
    bin_len: int, bin_idx: int, expected_end: int,
) -> None:
    assert calc_bin_end(bin_len, bin_idx) == expected_end


@pytest.mark.parametrize(
    "bin_len,pos,expected_idx",
    [
        (10, 1, 0),
        (10, 10, 0),
        (10, 11, 1),
        (10, 20, 1),
        (10, 21, 2),
        (100, 1, 0),
        (100, 100, 0),
        (100, 101, 1),
        (100, 501, 5),
    ],
)
def test_calc_bin_index(
    bin_len: int, pos: int, expected_idx: int,
) -> None:
    assert calc_bin_index(bin_len, pos) == expected_idx


def test_all_regions_from_chrom() -> None:
    regions = [
        Region("chr1", 1, 10),
        Region("chr2", 1, 10),
        Region("chr1", 20, 30),
        Region("chr3", 1, 10),
    ]
    chr1_regions = all_regions_from_chrom(regions, "chr1")
    assert len(chr1_regions) == 2
    assert all(r.chrom == "chr1" for r in chr1_regions)


def test_unique_regions() -> None:
    regions = [
        Region("chr1", 1, 10),
        Region("chr1", 1, 10),
        Region("chr2", 1, 10),
        Region("chr1", 1, 10),
    ]
    unique = unique_regions(regions)
    assert len(unique) == 2


def test_total_length() -> None:
    regions = [
        BedRegion("chr1", 1, 10),  # length 10
        BedRegion("chr1", 20, 25),  # length 6
        BedRegion("chr2", 1, 5),  # length 5
    ]
    assert total_length(regions) == 21


def test_intersection() -> None:
    regions1 = [
        Region("chr1", 1, 10),
        Region("chr1", 20, 30),
    ]
    regions2 = [
        Region("chr1", 5, 15),
        Region("chr1", 25, 35),
    ]
    result = intersection(regions1, regions2)
    assert len(result) == 2
    assert result[0] == Region("chr1", 5, 10)
    assert result[1] == Region("chr1", 25, 30)


def test_intersection_no_overlap() -> None:
    regions1 = [Region("chr1", 1, 10)]
    regions2 = [Region("chr1", 20, 30)]
    result = intersection(regions1, regions2)
    assert len(result) == 0


def test_intersection_different_chroms() -> None:
    regions1 = [Region("chr1", 1, 10)]
    regions2 = [Region("chr2", 1, 10)]
    result = intersection(regions1, regions2)
    assert len(result) == 0


def test_union() -> None:
    regions1 = [Region("chr1", 1, 10), Region("chr1", 5, 15)]
    regions2 = [Region("chr1", 20, 30)]
    result = union(regions1, regions2)
    # Should collapse overlapping regions
    assert len(result) >= 2


def test_difference() -> None:
    regions1 = [Region("chr1", 1, 100)]
    regions2 = [Region("chr1", 20, 30)]
    result = difference(regions1, regions2)
    assert len(result) == 2
    assert result[0] == Region("chr1", 1, 19)
    assert result[1] == Region("chr1", 31, 100)


def test_difference_no_overlap() -> None:
    regions1 = [Region("chr1", 1, 10)]
    regions2 = [Region("chr1", 20, 30)]
    result = difference(regions1, regions2)
    assert len(result) == 1
    assert result[0] == Region("chr1", 1, 10)


def test_difference_symmetric() -> None:
    regions1 = [Region("chr1", 1, 20)]
    regions2 = [Region("chr1", 10, 30)]
    result = difference(regions1, regions2, symmetric=True)
    # Should include non-overlapping parts from both
    assert len(result) == 2


def test_connected_component() -> None:
    regions = [
        BedRegion("chr1", 1, 10),
        BedRegion("chr1", 5, 15),
        BedRegion("chr1", 20, 30),
    ]
    components = list(connected_component(regions))
    assert len(components) == 2  # Two connected components


def test_region_str() -> None:
    reg = Region("chr1", 10, 20)
    assert str(reg) == "chr1:10-20"

    reg_no_end = Region("chr1", 10)
    assert str(reg_no_end) == "chr1:10"

    reg_no_start = Region("chr1")
    assert str(reg_no_start) == "chr1"


def test_region_repr() -> None:
    reg = Region("chr1", 10, 20)
    repr_str = repr(reg)
    assert "chr1" in repr_str
    assert "10" in repr_str
    assert "20" in repr_str


def test_region_equality() -> None:
    reg1 = Region("chr1", 10, 20)
    reg2 = Region("chr1", 10, 20)
    reg3 = Region("chr1", 10, 30)
    assert reg1 == reg2
    assert reg1 != reg3


def test_region_hash() -> None:
    reg1 = Region("chr1", 10, 20)
    reg2 = Region("chr1", 10, 20)
    reg3 = Region("chr1", 10, 30)
    # Same regions should have same hash
    assert hash(reg1) == hash(reg2)
    # Different regions might have different hash (not guaranteed but likely)
    assert hash(reg1) != hash(reg3)


def test_region_isin_position() -> None:
    reg = Region("chr1", 10, 20)
    assert reg.isin("chr1", 10)
    assert reg.isin("chr1", 15)
    assert reg.isin("chr1", 20)
    assert not reg.isin("chr1", 9)
    assert not reg.isin("chr1", 21)
    assert not reg.isin("chr2", 15)


def test_region_isin_with_none_boundaries() -> None:
    # Test region with no start
    reg = Region("chr1", None, 20)
    assert reg.isin("chr1", 1)
    assert reg.isin("chr1", 20)
    assert not reg.isin("chr1", 21)

    # Test region with no stop
    reg = Region("chr1", 10, None)
    assert reg.isin("chr1", 10)
    assert reg.isin("chr1", 100000)
    assert not reg.isin("chr1", 9)

    # Test region with no boundaries
    reg = Region("chr1", None, None)
    assert reg.isin("chr1", 1)
    assert reg.isin("chr1", 100000)


def test_region_init_invalid_types() -> None:
    with pytest.raises(TypeError):
        Region("chr1", "10", 20)  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        Region("chr1", 10, "20")  # type: ignore[arg-type]


def test_region_init_invalid_range() -> None:
    with pytest.raises(AssertionError):
        Region("chr1", 20, 10)  # start > stop


def test_region_begin_end_aliases() -> None:
    reg = Region("chr1", 10, 20)
    assert reg.begin == reg.start
    assert reg.end == reg.stop


def test_bed_region_init_assertions() -> None:
    # Valid BedRegion
    bed = BedRegion("chr1", 10, 20)
    assert bed.start == 10
    assert bed.stop == 20

    # Valid with same start and stop
    bed = BedRegion("chr1", 10, 10)
    assert bed.start == 10
    assert bed.stop == 10

    # Invalid condition stop < start
    with pytest.raises(AssertionError):
        BedRegion("chr1", 20, 10)


def test_bed_region_from_str_invalid() -> None:
    # BedRegion requires both start and stop
    with pytest.raises(ValueError, match="Invalid region format"):
        BedRegion.from_str("chr1")


def test_bed_region_begin_end_aliases() -> None:
    bed = BedRegion("chr1", 10, 20)
    assert bed.begin == bed.start
    assert bed.end == bed.stop


def test_collapse_overlapping_regions() -> None:
    regions = [
        Region("chr1", 1, 10),
        Region("chr1", 5, 15),
        Region("chr1", 12, 20),
    ]
    result = collapse(regions)
    assert len(result) == 1
    assert result[0] == Region("chr1", 1, 20)


def test_collapse_multiple_chromosomes() -> None:
    regions = [
        Region("chr1", 1, 10),
        Region("chr2", 5, 15),
        Region("chr1", 20, 30),
        Region("chr2", 25, 35),  # Changed to not overlap with chr2 region
    ]
    result = collapse(regions)
    assert len(result) == 4  # No collapse across chromosomes


def test_collapse_no_chrom_overlapping() -> None:
    regions = [
        BedRegion("chr1", 1, 10),
        BedRegion("chr1", 5, 15),
        BedRegion("chr1", 12, 20),
    ]
    result = collapse_no_chrom(regions)
    assert len(result) == 1
    assert result[0] == BedRegion("chr1", 1, 20)


def test_intersection_partial_overlap() -> None:
    regions1 = [Region("chr1", 1, 20)]
    regions2 = [Region("chr1", 10, 30)]
    result = intersection(regions1, regions2)
    assert len(result) == 1
    assert result[0] == Region("chr1", 10, 20)


def test_intersection_complete_overlap() -> None:
    regions1 = [Region("chr1", 1, 30)]
    regions2 = [Region("chr1", 10, 20)]
    result = intersection(regions1, regions2)
    assert len(result) == 1
    assert result[0] == Region("chr1", 10, 20)


def test_intersection_multiple_regions() -> None:
    regions1 = [
        Region("chr1", 1, 10),
        Region("chr1", 20, 30),
        Region("chr1", 40, 50),
    ]
    regions2 = [
        Region("chr1", 5, 25),
        Region("chr1", 45, 55),
    ]
    result = intersection(regions1, regions2)
    assert len(result) == 3


def test_union_empty_lists() -> None:
    result = union([])
    assert len(result) == 0


def test_union_single_list() -> None:
    regions = [Region("chr1", 1, 10), Region("chr1", 20, 30)]
    result = union(regions)
    assert len(result) == 2


def test_union_multiple_lists() -> None:
    regions1 = [Region("chr1", 1, 10)]
    regions2 = [Region("chr1", 5, 15)]
    regions3 = [Region("chr1", 20, 30)]
    result = union(regions1, regions2, regions3)
    # Should collapse overlapping regions
    assert len(result) == 2


def test_difference_complete() -> None:
    regions1 = [Region("chr1", 1, 30)]
    regions2 = [Region("chr1", 10, 20)]
    result = difference(regions1, regions2)
    assert len(result) == 2
    assert result[0] == Region("chr1", 1, 9)
    assert result[1] == Region("chr1", 21, 30)


def test_difference_partial() -> None:
    regions1 = [Region("chr1", 1, 20)]
    regions2 = [Region("chr1", 15, 30)]
    result = difference(regions1, regions2)
    assert len(result) == 1
    assert result[0] == Region("chr1", 1, 14)


def test_difference_empty() -> None:
    regions1 = [Region("chr1", 1, 10)]
    regions2 = [Region("chr1", 20, 30)]
    result = difference(regions1, regions2)
    assert len(result) == 1
    assert result[0] == Region("chr1", 1, 10)


def test_difference_symmetric_mode() -> None:
    regions1 = [Region("chr1", 1, 20)]
    regions2 = [Region("chr1", 15, 30)]
    result = difference(regions1, regions2, symmetric=True)
    # Should include non-overlapping parts from both
    assert len(result) == 2


def test_connected_component_single() -> None:
    regions = [BedRegion("chr1", 1, 10)]
    components = list(connected_component(regions))
    assert len(components) == 1


def test_connected_component_separate() -> None:
    regions = [
        BedRegion("chr1", 1, 10),
        BedRegion("chr1", 20, 30),
    ]
    components = list(connected_component(regions))
    assert len(components) == 2


def test_connected_component_overlapping() -> None:
    regions = [
        BedRegion("chr1", 1, 10),
        BedRegion("chr1", 5, 15),
    ]
    components = list(connected_component(regions))
    assert len(components) == 1


def test_all_regions_from_chrom_empty() -> None:
    result = all_regions_from_chrom([], "chr1")
    assert result == []


def test_all_regions_from_chrom_no_match() -> None:
    regions = [Region("chr2", 1, 10)]
    result = all_regions_from_chrom(regions, "chr1")
    assert result == []


def test_unique_regions_no_duplicates() -> None:
    regions = [
        Region("chr1", 1, 10),
        Region("chr2", 1, 10),
    ]
    result = unique_regions(regions)
    assert len(result) == 2


def test_unique_regions_all_duplicates() -> None:
    regions = [
        Region("chr1", 1, 10),
        Region("chr1", 1, 10),
        Region("chr1", 1, 10),
    ]
    result = unique_regions(regions)
    assert len(result) == 1


def test_total_length_empty() -> None:
    assert total_length([]) == 0


def test_total_length_single() -> None:
    regions = [BedRegion("chr1", 1, 10)]
    assert total_length(regions) == 10


def test_total_length_multiple() -> None:
    regions = [
        BedRegion("chr1", 1, 10),
        BedRegion("chr1", 20, 30),
        BedRegion("chr2", 1, 5),
    ]
    assert total_length(regions) == 26  # 10 + 11 + 5


def test_coalesce_first_non_none() -> None:
    assert coalesce(5, 10) == 5


def test_coalesce_first_is_none() -> None:
    assert coalesce(None, 10) == 10


def test_coalesce_first_is_zero() -> None:
    assert coalesce(0, 10) == 0


def test_bedfile2regions_multiple_comments(tmp_path: pathlib.Path) -> None:
    bed_file = tmp_path / "test.bed"
    bed_file.write_text(
        "# Comment 1\n# Comment 2\nchr1\t0\t100\n# Comment 3\nchr2\t50\t150\n",
    )

    regions = bedfile2regions(str(bed_file))
    assert len(regions) == 2


def test_regions2bedfile_single_region(tmp_path: pathlib.Path) -> None:
    regions = [BedRegion("chr1", 1, 100)]
    output_file = tmp_path / "output.bed"

    regions2bedfile(regions, str(output_file))

    content = output_file.read_text()
    assert "chr1\t0\t100\n" in content


def test_regions2bedfile_multiple_chroms(tmp_path: pathlib.Path) -> None:
    regions = [
        BedRegion("chr1", 1, 100),
        BedRegion("chr2", 50, 150),
        BedRegion("chrX", 1000, 2000),
    ]
    output_file = tmp_path / "output.bed"

    regions2bedfile(regions, str(output_file))

    content = output_file.read_text()
    assert "chr1\t0\t100\n" in content
    assert "chr2\t49\t150\n" in content
    assert "chrX\t999\t2000\n" in content


def test_split_into_regions_large_bin() -> None:
    # When region_size > chrom_length, should return single region
    regions = split_into_regions("chr1", 1000, 5000)
    assert len(regions) == 1
    assert regions[0] == Region("chr1", 1, 1000)


def test_region_intersection_method_none_boundaries() -> None:
    # Region with no boundaries contains everything
    reg1 = Region("chr1", None, None)
    reg2 = Region("chr1", 10, 20)
    result = reg1.intersection(reg2)
    assert result == Region("chr1", 10, 20)

    # Reverse
    result = reg2.intersection(reg1)
    assert result == Region("chr1", 10, 20)


def test_region_intersection_method_no_start() -> None:
    reg1 = Region("chr1", None, 50)
    reg2 = Region("chr1", 10, 20)
    result = reg1.intersection(reg2)
    assert result == Region("chr1", 10, 20)


def test_region_intersection_method_no_stop() -> None:
    reg1 = Region("chr1", 10, None)
    reg2 = Region("chr1", 5, 20)
    result = reg1.intersection(reg2)
    assert result == Region("chr1", 10, 20)


def test_region_contains_none_boundaries() -> None:
    # Region with no boundaries contains everything
    reg1 = Region("chr1", None, None)
    reg2 = Region("chr1", 10, 20)
    assert reg1.contains(reg2)

    # Region without start
    reg1 = Region("chr1", None, 50)
    reg2 = Region("chr1", 10, 20)
    assert reg1.contains(reg2)

    # Region without stop
    reg1 = Region("chr1", 10, None)
    reg2 = Region("chr1", 20, 30)
    assert reg1.contains(reg2)


def test_region_intersects_none_boundaries() -> None:
    # Region with no boundaries intersects everything
    reg1 = Region("chr1", None, None)
    reg2 = Region("chr1", 10, 20)
    assert reg1.intersects(reg2)

    # Region without stop
    reg1 = Region("chr1", 10, None)
    reg2 = Region("chr1", 5, 15)
    assert reg1.intersects(reg2)

    # No intersection
    reg1 = Region("chr1", None, 5)
    reg2 = Region("chr1", 10, 20)
    assert not reg1.intersects(reg2)


def test_calc_bin_edge_cases() -> None:
    # Test bin_idx = 0
    assert calc_bin_begin(1, 0) == 1
    assert calc_bin_end(1, 0) == 1
    assert calc_bin_index(1, 1) == 0

    # Large bin size
    assert calc_bin_begin(1000000, 5) == 5000001
    assert calc_bin_end(1000000, 5) == 6000000


def test_region_str_formats() -> None:
    # All values present
    reg = Region("chr1", 10, 20)
    assert str(reg) == "chr1:10-20"

    # Only start
    reg = Region("chr1", 10, None)
    assert str(reg) == "chr1:10"

    # No coordinates
    reg = Region("chr1", None, None)
    assert str(reg) == "chr1"


def test_region_from_str_edge_cases() -> None:
    # Chromosome only
    reg = Region.from_str("chrX")
    assert reg.chrom == "chrX"
    assert reg.start is None
    assert reg.stop is None

    # Single position (becomes BedRegion with same start/stop)
    reg = Region.from_str("chr1:100")
    assert isinstance(reg, BedRegion)
    assert reg.start == 100
    assert reg.stop == 100


def test_region_ne_operator() -> None:
    reg1 = Region("chr1", 10, 20)
    reg2 = Region("chr1", 10, 30)
    assert reg1 != reg2

    reg3 = Region("chr1", 10, 20)
    assert not reg1 != reg3  # noqa


def test_bed_region_stop_property() -> None:
    bed_reg = BedRegion("chr1", 10, 20)
    assert bed_reg.stop == 20
    assert bed_reg.end == 20


def test_bed_region_len() -> None:
    bed_reg = BedRegion("chr1", 10, 20)
    assert len(bed_reg) == 11  # inclusive range


def test_collapse_empty_list() -> None:
    result = collapse([])
    assert len(result) == 0


def test_collapse_single_region() -> None:
    regions = [Region("chr1", 1, 10)]
    result = collapse(regions)
    assert len(result) == 1
    assert result[0] == Region("chr1", 1, 10)


def test_collapse_no_chrom_empty() -> None:
    result = collapse_no_chrom([])
    assert result == []


def test_collapse_no_chrom_single() -> None:
    regions = [BedRegion("chr1", 1, 10)]
    result = collapse_no_chrom(regions)
    assert len(result) == 1


def test_collapse_sorted_flag() -> None:
    regions = [
        Region("chr1", 1, 10),
        Region("chr1", 5, 15),
    ]
    result = collapse(regions, is_sorted=True)
    assert len(result) == 1
    assert result[0] == Region("chr1", 1, 15)


def test_region_isin_position2() -> None:
    reg = Region("chr1", 10, 20)
    assert reg.isin("chr1", 10)
    assert reg.isin("chr1", 15)
    assert reg.isin("chr1", 20)
    assert not reg.isin("chr1", 9)
    assert not reg.isin("chr1", 21)
    assert not reg.isin("chr2", 15)


# Additional tests for uncovered branches


def test_region_equality_with_non_region() -> None:
    """Test __eq__ with non-Region objects."""
    reg = Region("chr1", 10, 20)
    assert not reg == "chr1:10-20"  # String  # noqa
    assert not reg == 123  # Integer  # noqa
    assert not reg == None  # None  # noqa
    assert not reg == ["chr1", 10, 20]  # List  # noqa


def test_region_make_region_edge_cases() -> None:
    """Test _make_region static method edge cases."""
    # Test with None chrom
    result = Region._make_region(None, 10, 20)  # type: ignore[arg-type]
    assert result is None

    # Test with start > stop
    result = Region._make_region("chr1", 20, 10)
    assert result is None

    # Test valid region
    result = Region._make_region("chr1", 10, 20)
    assert result is not None
    assert result.chrom == "chr1"
    assert result.start == 10
    assert result.stop == 20


def test_region_intersection_no_overlap_different_positions() -> None:
    """Test intersection when regions don't overlap."""
    reg1 = Region("chr1", 1, 10)
    reg2 = Region("chr1", 20, 30)
    result = reg1.intersection(reg2)
    assert result is None


def test_region_intersection_with_none_start_overlap() -> None:
    """Test intersection edge case with None boundaries."""
    # Region with no start intersecting with bounded region
    reg1 = Region("chr1", None, 50)
    reg2 = Region("chr1", 60, 70)
    result = reg1.intersection(reg2)
    assert result is None  # No overlap since reg2.start > reg1.stop


def test_region_contains_edge_cases_with_none() -> None:
    """Test contains method edge cases."""
    # Region without start, other without stop
    reg1 = Region("chr1", None, 50)
    reg2 = Region("chr1", 10, None)
    assert not reg1.contains(reg2)

    # Region without stop, other without start
    reg1 = Region("chr1", 10, None)
    reg2 = Region("chr1", None, 50)
    assert not reg1.contains(reg2)


def test_region_intersects_edge_case_stop_only() -> None:
    """Test intersects with only stop defined."""
    reg1 = Region("chr1", None, 50)
    reg2 = Region("chr1", None, None)
    assert reg1.intersects(reg2)

    # No intersection case
    reg1 = Region("chr1", None, 10)
    reg2 = Region("chr1", 20, 30)
    assert not reg1.intersects(reg2)


def test_region_intersects_edge_case_start_only() -> None:
    """Test intersects with only start defined."""
    reg1 = Region("chr1", 50, None)
    reg2 = Region("chr1", 10, 20)
    assert not reg1.intersects(reg2)

    reg1 = Region("chr1", 50, None)
    reg2 = Region("chr1", None, None)
    assert reg1.intersects(reg2)


def test_region_from_str_invalid_format() -> None:
    """Test from_str with invalid format."""
    with pytest.raises(ValueError, match="unexpeced format"):
        Region.from_str("chr1:10-20-30")


def test_collapse_extending_region_edge_case() -> None:
    """Test collapse when a region extends the previous one."""
    regions = [
        Region("chr1", 1, 10),
        Region("chr1", 8, 15),  # Overlaps and extends
        Region("chr1", 14, 20),  # Overlaps and extends further
    ]
    result = collapse(regions)
    assert len(result) == 1
    assert result[0] == Region("chr1", 1, 20)


def test_collapse_not_extending() -> None:
    """Test collapse when overlapping but not extending."""
    regions = [
        Region("chr1", 1, 20),
        Region("chr1", 5, 15),  # Contained, doesn't extend
    ]
    result = collapse(regions)
    assert len(result) == 1
    assert result[0] == Region("chr1", 1, 20)


def test_collapse_no_chrom_not_extending() -> None:
    """Test collapse_no_chrom when overlapping but not extending."""
    regions = [
        BedRegion("chr1", 1, 20),
        BedRegion("chr1", 5, 15),  # Contained, doesn't extend
    ]
    result = collapse_no_chrom(regions)
    assert len(result) == 1
    assert result[0] == BedRegion("chr1", 1, 20)


def test_collapse_no_chrom_extending() -> None:
    """Test collapse_no_chrom when a region extends the previous one."""
    regions = [
        BedRegion("chr1", 1, 10),
        BedRegion("chr1", 8, 15),  # Overlaps and extends
    ]
    result = collapse_no_chrom(regions)
    assert len(result) == 1
    assert result[0] == BedRegion("chr1", 1, 15)


def test_intersection_complex_scenarios() -> None:
    """Test intersection function with complex scenarios."""
    # Test when s2 region completely contains s1 region
    regions1 = [Region("chr1", 5, 10)]
    regions2 = [Region("chr1", 1, 20)]
    result = intersection(regions1, regions2)
    assert len(result) == 1
    assert result[0] == Region("chr1", 5, 10)

    # Test when regions from different chromosomes are compared
    regions1 = [Region("chr1", 1, 10), Region("chr3", 1, 10)]
    regions2 = [Region("chr2", 1, 10)]
    result = intersection(regions1, regions2)
    assert len(result) == 0


def test_intersection_partial_overlap_cases() -> None:
    """Test intersection with various partial overlap scenarios."""
    # s2 region starts before s1 but ends inside s1
    regions1 = [Region("chr1", 10, 20)]
    regions2 = [Region("chr1", 5, 15)]
    result = intersection(regions1, regions2)
    assert len(result) == 1
    assert result[0] == Region("chr1", 10, 15)

    # s2 region starts inside s1 and ends after s1
    regions1 = [Region("chr1", 10, 20)]
    regions2 = [Region("chr1", 15, 25)]
    result = intersection(regions1, regions2)
    assert len(result) == 1
    assert result[0] == Region("chr1", 15, 20)


def test_diff_function_edge_cases() -> None:
    """Test _diff function with various edge cases."""
    # Test when regions_a runs past regions_b
    regions_a = [Region("chr1", 1, 10), Region("chr1", 20, 30)]
    regions_b = [Region("chr1", 5, 8)]
    result = _diff(regions_a, regions_b)
    assert len(result) >= 2

    # Test with different chromosomes (chr1 < chr2 < chr3)
    # chr3 region won't be in result since chr2 breaks the loop
    regions_a = [Region("chr1", 1, 10), Region("chr3", 1, 10)]
    regions_b = [Region("chr2", 1, 10)]
    result = _diff(regions_a, regions_b)
    assert len(result) >= 1
    assert any(r.chrom == "chr1" for r in result)

    # Test when reg_a.stop < regions_b[k].start
    regions_a = [Region("chr1", 1, 10), Region("chr1", 30, 40)]
    regions_b = [Region("chr1", 20, 25)]
    result = _diff(regions_a, regions_b)
    assert len(result) == 2


def test_diff_with_multiple_subtractions() -> None:
    """Test _diff when multiple regions_b overlap with one reg_a."""
    # One large region with multiple holes
    regions_a = [Region("chr1", 1, 100)]
    regions_b = [
        Region("chr1", 10, 20),
        Region("chr1", 30, 40),
        Region("chr1", 50, 60),
    ]
    result = _diff(regions_a, regions_b)
    # Should have gaps between the subtractions
    assert len(result) > 1


def test_diff_with_chromosome_mismatch() -> None:
    """Test _diff when chromosomes don't match mid-iteration."""
    regions_a = [
        Region("chr1", 1, 100),
        Region("chr2", 1, 100),
    ]
    regions_b = [
        Region("chr1", 10, 20),
        Region("chr3", 10, 20),  # Different chromosome
    ]
    result = _diff(regions_a, regions_b)
    # chr2 region should remain since it doesn't match chr3
    assert any(r.chrom == "chr2" for r in result)
