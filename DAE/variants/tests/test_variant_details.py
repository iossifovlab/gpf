'''
Created on Mar 30, 2018

@author: lubo
'''
import pytest
from variants.variant import VariantDetail
from variants.attributes import VariantType


@pytest.mark.parametrize("variant,variant_type,position", [
    ("1:1558774:G:A", VariantType.substitution, 1558774),
    ("1:874816:CCCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT:C",
     VariantType.deletion, 874817),
    ("1:874816:CCCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT:"
     "CTCCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT",
     VariantType.insertion, 874817),
    ("1:874816:CCCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT:"
     "CCCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT"
     "CCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT",
     VariantType.insertion, 874866),

])
def test_variant_effect_annotation(variant, variant_type, position):
    print(variant)
    [chrom, pos, ref, alts] = variant.split(":")
    details = VariantDetail.from_vcf(chrom, int(pos), ref, alts.split(','))
    print(details)
    for detail in details:
        assert detail.variant_type == variant_type
        assert detail.cshl_position == position


@pytest.mark.slow
@pytest.mark.parametrize("variant_types,query", [
    (set([VariantType.substitution]), "sub"),
    (set([VariantType.deletion, VariantType.insertion]), "del or ins"),
    (set([VariantType.complex]), "complex"),
])
def test_query_by_variant_type(nvcf19f, variant_types, query):
    vs = nvcf19f.query_variants(
        variant_type=query)
    vs = list(vs)

    assert len(vs) > 0
    for v in vs:
        vts = set([ad.variant_type for ad in v.alt_details])
        assert variant_types.intersection(vts)
