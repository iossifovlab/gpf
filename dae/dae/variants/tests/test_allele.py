import pytest

from dae.variants.core import Allele


def test_position_allele():
    a = Allele.build_position_allele("1", 3)
    assert a.allele_type == Allele.Type.position
    assert a.end_position == 3


@pytest.mark.parametrize("allele,end_position,allele_type", [
    (("1", 1, "C", "A"), 1, Allele.Type.substitution),
    (("1", 1, "C", "CA"), 1, Allele.Type.small_insertion),
    (("1", 1, "CA", "C"), 2, Allele.Type.small_deletion),
    (("1", 1, "CA", "AC"), 2, Allele.Type.complex),
    (("1", 1, "C", None), 1, Allele.Type.position),
])
def test_vcf_allele(allele, end_position, allele_type):
    a = Allele.build_vcf_allele(*allele)
    assert a.position == 1
    assert a.end_position == end_position
    assert a.allele_type == allele_type
