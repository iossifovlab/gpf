import pytest
import pysam
from dae.utils.regions import Region, collapse, collapse_no_chrom, \
    split_into_regions, get_chromosome_length

from dae.genomic_resources.testing import setup_tabix


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
    ],
)
def test_parse_regions(region, expected):
    result = Region.from_str(region)
    # assert result is not None
    assert result == expected


@pytest.mark.parametrize(
    "regions,expected",
    [
        ("1:1-2,1:1-3", [Region("1", 1, 3)]),
        ("1:1-2,1:2-3", [Region("1", 1, 3)]),
        ("1:1-2,2:2-3", [Region("1", 1, 2), Region("2", 2, 3)]),
        ("1:1-2,1:3-4", [Region("1", 1, 2), Region("1", 3, 4)]),
    ],
)
def test_collapse_simple(regions, expected):
    regions = [Region.from_str(r) for r in regions.split(",")]
    result = collapse(regions)

    assert len(result) == len(expected)
    for res, exp in zip(result, expected):
        assert res == exp


@pytest.mark.parametrize(
    "regions,expected",
    [
        ("1:1-2,1:1-3", [Region("1", 1, 3)]),
        ("1:1-2,1:2-3", [Region("1", 1, 3)]),
        ("1:1-2,1:3-4", [Region("1", 1, 2), Region("1", 3, 4)]),
    ],
)
def test_collapse_no_chrom_simple(regions, expected):
    regions = [Region.from_str(r) for r in regions.split(",")]
    result = collapse_no_chrom(regions)

    assert len(result) == len(expected)
    for res, exp in zip(result, expected):
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
            Region("1", 4, 4)
        ]),
    ]
)
def test_split_into_regions(chrom, chrom_length, region_size, expected):
    result = split_into_regions(chrom, chrom_length, region_size)

    assert len(result) == len(expected)

    for i in range(len(result)):
        assert result[i] == expected[i], f"{result[i]} != {expected[i]}"


@pytest.fixture()
def sample_tabix(tmp_path):
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
        """, seq_col=0, start_col=1, end_col=2
    )
    return pysam.TabixFile(str(filepath))


@pytest.mark.parametrize(
    "precision",
    [
        5_000_000,
        1000,
        100,
        1,
    ]
)
def test_get_chrom_length(sample_tabix, precision):
    one_length = get_chromosome_length(sample_tabix, "1", precision=precision)
    assert one_length > 14
    assert one_length - 14 <= precision
    two_length = get_chromosome_length(sample_tabix, "2", precision=precision)
    assert two_length > 4
    assert two_length - 14 <= precision
    three_length = get_chromosome_length(
        sample_tabix, "3", precision=precision
    )
    assert three_length > 500_010
    assert three_length - 500_010 <= precision
