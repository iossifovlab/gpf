# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.annotation.annotatable import Annotatable, Position, Region, \
    VCFAllele, CNVAllele
from dae.utils.variant_utils import trim_parsimonious


@pytest.mark.parametrize(
    "allele,allele_type", [
        (
            ("1", 1, "C", "A"),
            Annotatable.Type.SUBSTITUTION),
        (
            ("1", 1, "C", "CA"),
            Annotatable.Type.SMALL_INSERTION),
        (
            ("1", 1, "CA", "C"),
            Annotatable.Type.SMALL_DELETION),
        (
            ("1", 1, "CA", "AC"),
            Annotatable.Type.COMPLEX),
        (
            ("1", 1, "GAA", "AAA"),
            Annotatable.Type.COMPLEX
        ),
    ]
)
def test_vcf_allele(allele, allele_type):  # type: ignore
    annotatable = VCFAllele(*allele)
    assert annotatable.type == allele_type


@pytest.mark.parametrize("allele,expected,length,end_pos,allele_type", [
    ((1, "AA", "CA"), (1, "A", "C"), 1, 1, VCFAllele.Type.SUBSTITUTION),
    ((1, "CA", "CT"), (2, "A", "T"), 1, 2, VCFAllele.Type.SUBSTITUTION),
    ((1, "ACA", "A"), (1, "ACA", "A"), 4, 4, VCFAllele.Type.SMALL_DELETION),
    ((1, "AACA", "AA"), (1, "AAC", "A"), 4, 4, VCFAllele.Type.SMALL_DELETION),
    ((4, "GCAT", "GTGC"), (5, "CAT", "TGC"), 4, 8, VCFAllele.Type.COMPLEX),
    ((5, "CATG", "TGCG"), (5, "CAT", "TGC"), 4, 8, VCFAllele.Type.COMPLEX),
    ((4, "GCATG", "GTGCG"), (5, "CAT", "TGC"), 4, 8, VCFAllele.Type.COMPLEX),
    ((4, "GG", "GAGG"), (4, "G", "GAG"), 2, 5, VCFAllele.Type.SMALL_INSERTION),
    (
        (100, "TGGTGCAGGC", "T"),
        (100, "TGGTGCAGGC", "T"),
        11, 110, VCFAllele.Type.SMALL_DELETION
    ),
    (
        (100, "TGGTGCAGGC", "CGGTGCAGGC"),
        (100, "T", "C"),
        1, 109, VCFAllele.Type.SUBSTITUTION
    ),
    (
        (100, "TGGTGCAGGC", "TGGTGCAGGCGGTGCAGGC"),
        (100, "T", "TGGTGCAGGC"),
        2, 101, VCFAllele.Type.SMALL_INSERTION),
    (
        (100, "TGGTGCAGGC", "TGGTGCAGGT"),
        (109, "C", "T"),
        1, 109, VCFAllele.Type.SUBSTITUTION
    ),
])
def test_parsimonious_vcf_allele(  # type: ignore
        allele, expected, length, end_pos, allele_type):

    parsimonious = trim_parsimonious(*allele)
    annotatable = VCFAllele("1", *parsimonious)

    assert annotatable.type == allele_type
    assert len(annotatable) == length
    assert annotatable.pos == expected[0]
    assert annotatable.ref == expected[1]
    assert annotatable.alt == expected[2]


@pytest.mark.parametrize(
    "value,expected", [
        ("Position(chr1, 123)", Position("chr1", 123)),
        ("POSITION(chr1, 123)", Position("chr1", 123)),
    ]
)
def test_annotatable_from_string_position(value, expected):  # type: ignore
    assert Annotatable.from_string(value) == expected


@pytest.mark.parametrize(
    "value,expected", [
        ("Region(chr1, 123, 456)", Region("chr1", 123, 456)),
        ("REGION(chr1, 123, 456)", Region("chr1", 123, 456)),
    ]
)
def test_annotatable_from_string_region(value, expected):  # type: ignore
    assert Annotatable.from_string(value) == expected


@pytest.mark.parametrize(
    "value,expected", [
        ("VCFAllele(chr1, 123, A, G)", VCFAllele("chr1", 123, "A", "G")),
        ("SUBSTITUTION(chr1, 123, A, G)", VCFAllele("chr1", 123, "A", "G")),
        ("COMPLEX(chr1, 123, AC, GT)", VCFAllele("chr1", 123, "AC", "GT")),
        ("SMALL_DELETION(X, 1, AAA, A)", VCFAllele("X", 1, "AAA", "A")),
        ("SMALL_INSERTION(X, 1, A, AAA)", VCFAllele("X", 1, "A", "AAA")),
    ]
)
def test_annotatable_from_string_vcf(value, expected):  # type: ignore
    assert Annotatable.from_string(value) == expected


@pytest.mark.parametrize(
    "value,expected", [
        ("CNVAllele(X, 123, 345, LARGE_DUPLICATION)",
         CNVAllele("X", 123, 345, Annotatable.Type.LARGE_DUPLICATION)),
        ("CNVAllele(X, 123, 345, LARGE_DELETION)",
         CNVAllele("X", 123, 345, Annotatable.Type.LARGE_DELETION)),
        ("LARGE_DUPLICATION(X, 123, 345)",
         CNVAllele("X", 123, 345, Annotatable.Type.LARGE_DUPLICATION)),
        ("LARGE_DELETION(X, 123, 345)",
         CNVAllele("X", 123, 345, Annotatable.Type.LARGE_DELETION)),
    ]
)
def test_annotatable_from_string_cnv(value, expected):  # type: ignore
    assert Annotatable.from_string(value) == expected
