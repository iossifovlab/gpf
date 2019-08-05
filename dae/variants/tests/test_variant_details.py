'''
Created on Mar 30, 2018

@author: lubo
'''
import pytest
from dae.variants.variant import VariantDetail
from dae.variants.attributes import VariantType


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
def test_variant_details(variant, variant_type, position):
    print(variant)
    [chrom, pos, ref, alt] = variant.split(":")
    detail = VariantDetail.from_vcf(chrom, int(pos), ref, alt)
    print(detail)

    assert detail.variant_type == variant_type
    assert detail.cshl_position == position
