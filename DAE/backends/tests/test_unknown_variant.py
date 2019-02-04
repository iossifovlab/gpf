'''
Created on Mar 29, 2018

@author: lubo
'''
from __future__ import print_function, unicode_literals, absolute_import

import pytest

from RegionOperations import Region


@pytest.mark.parametrize("region,count,members", [
    (Region('1', 11500, 11500), 1, ['mom1', None, None]),
    (Region('1', 11501, 11501), 1, ['mom1', None, 'ch1']),
    (Region('1', 11502, 11502), 1, [None, None, 'ch1']),
    (Region('1', 11503, 11503), 1, ['mom1', 'dad1', 'ch1']),
])
def test_variant_in_members(variants_vcf, region, count, members):
    fvars = variants_vcf("fixtures/unknown_trio")
    vs = list(fvars.query_variants(regions=[region]))
    assert len(vs) == count
    for v in vs:
        for aa in v.alt_alleles:
            print(aa.variant_in_members, type(aa.variant_in_members))
            assert list(aa.variant_in_members) == members
