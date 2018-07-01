'''
Created on Mar 19, 2018

@author: lubo
'''
from __future__ import print_function

from variants.vcf_utils import mat2str
from variants.attributes import Role
from RegionOperations import Region


def test_members_in_order1_genotype_full(variants_vcf):
    fvars = variants_vcf("fixtures/members_in_order1")
    for v in fvars.query_variants():
        print(v, mat2str(v.best_st), mat2str(v.gt), v.inheritance)
        assert 'gpa' in v.variant_in_members
        assert Role.paternal_grandfather in v.variant_in_roles


def test_members_in_order2_genotype_full(variants_vcf):
    fvars = variants_vcf("fixtures/members_in_order2")
    for v in fvars.query_variants():
        print(v, mat2str(v.best_st), mat2str(v.gt), v.inheritance)
        assert 'gpa' in v.variant_in_members
        assert Role.paternal_grandfather in v.variant_in_roles


def test_freq_trios_2_full(variants_vcf):
    fvars = variants_vcf("fixtures/trios2")
    vs = list(fvars.query_variants(
        family_ids=['f1'], regions=[Region("1", 11539, 11540)]))
    assert len(vs) == 2

    v1 = vs[0]
    v2 = vs[1]

    print(v1, mat2str(v1.best_st), mat2str(v1.gt), v1.inheritance)
    # FIXME:
    #     assert v1.get_attr('all.nAltAlls')[1] == 2
    #     assert v1.get_attr('all.altFreq')[1] == 25

    assert Role.mom in v1.variant_in_roles
    assert 'mom1' in v1.variant_in_members

    print(v2, mat2str(v2.best_st), mat2str(v2.gt), v2.inheritance)
    # FIXME:
    #     assert v1.get_attr('all.nAltAlls')[1] == 2
    #     assert v1.get_attr('all.altFreq')[1] == 25
    assert Role.dad in v2.variant_in_roles
    assert 'dad1' in v2.variant_in_members
