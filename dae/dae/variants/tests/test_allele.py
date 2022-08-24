# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.variants.core import Allele
from dae.variants.variant import SummaryAllele, SummaryVariantFactory


def test_position_allele():
    allele = Allele.build_position_allele("1", 3)
    assert allele.allele_type == Allele.Type.position
    assert allele.end_position == 3


@pytest.mark.parametrize("allele,end_position,allele_type", [
    (("1", 1, "C", "A"), 1, Allele.Type.substitution),
    (("1", 1, "C", "CA"), 1, Allele.Type.small_insertion),
    (("1", 1, "CA", "C"), 2, Allele.Type.small_deletion),
    (("1", 1, "CA", "AC"), 2, Allele.Type.complex),
    (("1", 1, "C", None), 1, Allele.Type.position),
])
def test_vcf_allele(allele, end_position, allele_type):
    allele = Allele.build_vcf_allele(*allele)
    assert allele.position == 1
    assert allele.end_position == end_position
    assert allele.allele_type == allele_type


def test_to_records():
    effect = "synonymous!SAMD11:synonymous!NM_152486_1:SAMD11:synonymous:40/68"
    in_allele = SummaryAllele(
        "1", 11539, "T", "G", 0, 1,
        effect=effect
    )
    records = in_allele.to_record
    out_allele = SummaryVariantFactory.summary_allele_from_record(records)

    assert in_allele.summary_index == out_allele.summary_index
    assert in_allele.allele_index == out_allele.allele_index
    assert in_allele.variant_type == out_allele.variant_type
    assert in_allele.transmission_type == out_allele.transmission_type
    assert in_allele.effects == out_allele.effects
    assert in_allele.details.chrom == out_allele.details.chrom
    assert str(in_allele) == str(out_allele)
