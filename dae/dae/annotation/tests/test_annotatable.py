import pytest

from dae.annotation.annotatable import Annotatable, VCFAllele
from dae.utils.variant_utils import trim_parsimonious


@pytest.mark.parametrize(
    "allele,allele_type", [
        (
            ("1", 1, "C", "A"),
            Annotatable.Type.substitution),
        (
            ("1", 1, "C", "CA"),
            Annotatable.Type.small_insertion),
        (
            ("1", 1, "CA", "C"),
            Annotatable.Type.small_deletion),
        (
            ("1", 1, "CA", "AC"),
            Annotatable.Type.complex),
        (
            ("1", 1, "GAA", "AAA"),
            Annotatable.Type.complex
        ),
    ]
)
def test_vcf_allele(allele, allele_type):

    a = VCFAllele(*allele)

    assert a.type == allele_type


@pytest.mark.parametrize("allele,exprected,length,end_pos,allele_type", [
    ((1, "AA", "CA"), (1, "A", "C"), 1, 1, VCFAllele.Type.substitution),
    ((1, "CA", "CT"), (2, "A", "T"), 1, 2, VCFAllele.Type.substitution),
    ((1, "ACA", "A"), (1, "ACA", "A"), 4, 4, VCFAllele.Type.small_deletion),
    ((1, "AACA", "AA"), (1, "AAC", "A"), 4, 4, VCFAllele.Type.small_deletion),
    ((4, "GCAT", "GTGC"), (5, "CAT", "TGC"), 4, 8, VCFAllele.Type.complex),
    ((5, "CATG", "TGCG"), (5, "CAT", "TGC"), 4, 8, VCFAllele.Type.complex),
    ((4, "GCATG", "GTGCG"), (5, "CAT", "TGC"), 4, 8, VCFAllele.Type.complex),
    ((4, "GG", "GAGG"), (4, "G", "GAG"), 2, 5, VCFAllele.Type.small_insertion),
    (
        (100, "TGGTGCAGGC", "T"),
        (100, "TGGTGCAGGC", "T"),
        11, 110, VCFAllele.Type.small_deletion
    ),
    (
        (100, "TGGTGCAGGC", "CGGTGCAGGC"),
        (100, "T", "C"),
        1, 109, VCFAllele.Type.substitution
    ),
    (
        (100, "TGGTGCAGGC", "TGGTGCAGGCGGTGCAGGC"),
        (100, "T", "TGGTGCAGGC"),
        2, 101, VCFAllele.Type.small_insertion),
    (
        (100, "TGGTGCAGGC", "TGGTGCAGGT"),
        (109, "C", "T"),
        1, 109, VCFAllele.Type.substitution
    ),
])
def test_parsimonious_vcf_allele(
        allele, expected, length, end_pos, allele_type):

    parsimonious = trim_parsimonious(*allele)
    a = VCFAllele("1", *parsimonious)

    assert a.type == allele_type
    assert len(a) == length
    assert a.pos == expected[0]
    assert a.ref == expected[1]
    assert a.alt == expected[2]
