import pytest
from dae.utils.regions import Region, collapse, collapse_no_chrom


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
