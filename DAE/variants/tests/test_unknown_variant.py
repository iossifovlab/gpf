'''
Created on Mar 29, 2018

@author: lubo
'''
from __future__ import print_function

import pytest
from RegionOperations import Region
from variants.vcf_utils import mat2str


@pytest.mark.parametrize("region,count,members", [
    (Region('1', 11500, 11500), 1, set(['mom1'])),
    (Region('1', 11501, 11501), 1, set(['mom1', 'ch1'])),
    (Region('1', 11502, 11502), 1, set(['ch1'])),
    (Region('1', 11503, 11503), 1, set(['mom1', 'dad1', 'ch1'])),
])
def test_variant_in_members(variants_vcf, region, count, members):
    fvars = variants_vcf("fixtures/unknown_trio")
    vs = list(fvars.query_variants(regions=[region]))
    assert len(vs) == count
    for v in vs:
        print(v, mat2str(v.best_st), v.inheritance)
        print(v.variant_in_members)
        print(v.variant_in_roles)
        print(v.variant_in_sexes)
        print(v.gt)
        assert v.variant_in_members == members
