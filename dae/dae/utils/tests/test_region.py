import pytest
from dae.utils.regions import Region


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
        ("chr1_KI270706v1_random", Region("chr1_KI270706v1_random")),
    ],
)
def test_parse_regions(region, expected):
    result = Region.from_str(region)
    # assert result is not None
    assert result == expected
