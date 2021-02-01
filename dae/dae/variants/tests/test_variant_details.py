"""
Created on Mar 30, 2018

@author: lubo
"""
import pytest
from dae.variants.variant import VariantDetail


@pytest.mark.parametrize(
    "variant,position",
    [
        ("1:1558774:G:A", 1558774),
        (
            "1:874816:CCCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT:C",
            874817,
        ),
        (
            "1:874816:CCCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT:"
            "CTCCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT",
            874817,
        ),
        (
            "1:874816:CCCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT:"
            "CCCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT"
            "CCCCTCATCACCTCCCCAGCCACGGTGAGGACCCACCCTGGCATGATCT",
            874817,
        ),
    ],
)
def test_variant_details(variant, position):
    print(variant)
    [chrom, pos, ref, alt] = variant.split(":")
    detail = VariantDetail.from_vcf(chrom, int(pos), ref, alt)
    print(detail)

    assert detail.cshl_position == position
