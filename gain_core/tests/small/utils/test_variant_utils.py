# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from gain.utils.variant_utils import (
    reverse_complement,
    trim_parsimonious,
    trim_str_left,
    trim_str_right,
)


@pytest.mark.parametrize("dna,expected", [
    ("a", "T"),
    ("ac", "GT"),
    ("actg", "CAGT"),
])
def test_reverse_complement(dna: str, expected: str) -> None:
    result = reverse_complement(dna)
    assert result == expected


@pytest.mark.parametrize("pos,ref,alt,trim_pos,trim_ref,trim_alt", [
    (1, "AA", "CA", 1, "A", "C"),
    (1, "AAA", "CCA", 1, "AA", "CC"),
    (1, "AAA", "ACA", 1, "AA", "AC"),
    (100, "TGGTGCAGGC", "T", 100, "TGGTGCAGGC", "T"),
    (100, "TGGTGCAGGC", "CGGTGCAGGC", 100, "T", "C"),
    (100, "TGGTGCAGGC", "TGGTGCAGGCGGTGCAGGC", 100, "T", "TGGTGCAGGC"),
    (100, "TGGTGCAGGC", "TGGTGCAGGT", 100, "TGGTGCAGGC", "TGGTGCAGGT"),
])
def test_trim_str_right(
    pos: int,
    ref: str,
    alt: str,
    trim_pos: int,
    trim_ref: str,
    trim_alt: str,
) -> None:
    tpos, tref, talt = trim_str_right(pos, ref, alt)
    assert trim_pos == tpos
    assert trim_ref == tref
    assert trim_alt == talt


@pytest.mark.parametrize("pos,ref,alt,trim_pos,trim_ref,trim_alt", [
    (1, "AA", "CA", 1, "AA", "CA"),
    (1, "AAA", "CCA", 1, "AAA", "CCA"),
    (1, "AAA", "ACA", 2, "AA", "CA"),
    (100, "TGGTGCAGGC", "T", 101, "GGTGCAGGC", ""),
    (100, "TGGTGCAGGC", "CGGTGCAGGC", 100, "TGGTGCAGGC", "CGGTGCAGGC"),
    (100, "TGGTGCAGGC", "TGGTGCAGGCGGTGCAGGC", 110, "", "GGTGCAGGC"),
    (100, "TGGTGCAGGC", "TGGTGCAGGT", 109, "C", "T"),
])
def test_trim_str_left(
    pos: int,
    ref: str,
    alt: str,
    trim_pos: int,
    trim_ref: str,
    trim_alt: str,
) -> None:
    tpos, tref, talt = trim_str_left(pos, ref, alt)
    assert trim_pos == tpos
    assert trim_ref == tref
    assert trim_alt == talt


@pytest.mark.parametrize("allele,parsimonious", [
    ((1, "AA", "CA"), (1, "A", "C")),
    ((1, "CA", "CT"), (2, "A", "T")),
    ((1, "ACA", "A"), (1, "ACA", "A")),
    ((1, "AACA", "AA"), (1, "AAC", "A")),
    ((4, "GCAT", "GTGC"), (5, "CAT", "TGC")),
    ((5, "CATG", "TGCG"), (5, "CAT", "TGC")),
    ((4, "GCATG", "GTGCG"), (5, "CAT", "TGC")),
    ((4, "GG", "GAGG"), (4, "G", "GAG")),
    ((100, "TGGTGCAGGC", "T"), (100, "TGGTGCAGGC", "T")),
    ((100, "TGGTGCAGGC", "CGGTGCAGGC"), (100, "T", "C")),
    ((100, "TGGTGCAGGC", "TGGTGCAGGCGGTGCAGGC"), (100, "T", "TGGTGCAGGC")),
    ((100, "TGGTGCAGGC", "TGGTGCAGGT"), (109, "C", "T")),
])
def test_trim_parsimonious(
    allele: tuple[int, str, str], parsimonious: tuple[int, str, str],
) -> None:
    pos, ref, alt = trim_parsimonious(*allele)

    assert (pos, ref, alt) == parsimonious
