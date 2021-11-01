import pytest

from dae.annotation.annotatable import Annotatable, VCFAllele


@pytest.mark.parametrize(
    "allele,pos_begin,pos_end,trim_pos,trim_ref,trim_alt,length,allele_type", [
        ((
            "1", 1, "C", "A"),      1, 1, 1, "C", "A", 1,
            Annotatable.Type.substitution),
        ((
            "1", 1, "C", "CA"),     1, 2, 2, "", "A", 2,
            Annotatable.Type.small_insertion),
        (
            ("1", 1, "CA", "C"),    1, 3, 2, "A", "", 3,
            Annotatable.Type.small_deletion),
        (
            ("1", 1, "CA", "AC"),   0, 3, 1, "CA", "AC", 4,
            Annotatable.Type.complex),
        (
            ("1", 1, "GAA", "AAA"), 1, 1, 1, "G", "A", 1,
            Annotatable.Type.substitution
        ),
    ]
)
def test_vcf_allele(
        allele, pos_begin, pos_end, trim_pos, trim_ref, trim_alt,
        length, allele_type):

    a = VCFAllele(*allele)

    assert a.type == allele_type
    assert a.pos_begin == pos_begin
    assert a.pos_end == pos_end

    assert a.ref == allele[2]
    assert a.alt == allele[3]
    assert a.pos == allele[1]

    assert a.trim_pos == trim_pos
    assert a.trim_ref == trim_ref
    assert a.trim_alt == trim_alt

    assert len(a) == length
