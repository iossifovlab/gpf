import pytest

from dae.utils.dae_utils import join_line, dna_complement


def test_join_line():
    assert join_line(
        ['1', 'a', '3.14', ['0', '1.23', 'b'], ["single"]]
    ) == "1\ta\t3.14\t0; 1.23; b\tsingle\n"


@pytest.mark.parametrize("dna,expected", [
    ("a", "T"),
    ("ac", "GT"),
    ("actg", "CAGT"),
])
def test_dna_complement(dna, expected):
    result = dna_complement(dna)
    assert result == expected
