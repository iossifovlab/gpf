'''
Created on Mar 19, 2018

@author: lubo
'''
from __future__ import print_function

# from variants.tests.conftest import relative_to_this_test_folder
# from variants.configure import Configure
# from icecream import ic
# from variants.raw_vcf import RawFamilyVariants
from variants.vcf_utils import mat2str
from variants.attributes import Role
from RegionOperations import Region
# import pytest


# def test_with_fixture_vcf_file(composite_annotator):
#     a_data = relative_to_this_test_folder("fixtures/a")
#     a_conf = Configure.from_prefix(a_data)
#     ic(a_conf)
#
#     fvars = RawFamilyVariants(a_conf, annotator=composite_annotator)
#     vs = fvars.query_variants()
#
#     for v in vs:
#         print(v, v.family_id, mat2str(v.best_st), mat2str(v.gt),
#               v.inheritance)


def test_members_in_order1_genotype(single_vcf):
    fvars = single_vcf("fixtures/members_in_order1")
    for v in fvars.query_variants():
        print(v, mat2str(v.best_st), mat2str(v.gt), v.inheritance)
        assert 'gpa' in v.variant_in_members
        assert Role.paternal_grandfather in v.variant_in_roles


def test_members_in_order2_genotype(single_vcf):
    fvars = single_vcf("fixtures/members_in_order2")
    for v in fvars.query_variants():
        print(v, mat2str(v.best_st), mat2str(v.gt), v.inheritance)
        assert 'gpa' in v.variant_in_members
        assert Role.paternal_grandfather in v.variant_in_roles


def test_freq_trios_2(single_vcf):
    fvars = single_vcf("fixtures/trios2")
    vs = list(fvars.query_variants(
        family_ids=['f1'], regions=[Region("1", 11539, 11540)]))
    assert len(vs) == 2

    v1 = vs[0]
    v2 = vs[1]

    print(v1, mat2str(v1.best_st), mat2str(v1.gt), v1.inheritance)
    assert v1.get_attr('all.nAltAlls')[1] == 2
    assert v1.get_attr('all.altFreq')[1] == 25

    assert Role.mom in v1.variant_in_roles
    assert 'mom1' in v1.variant_in_members

    print(v2, mat2str(v2.best_st), mat2str(v2.gt), v2.inheritance)
    assert v1.get_attr('all.nAltAlls')[1] == 2
    assert v1.get_attr('all.altFreq')[1] == 25
    assert Role.dad in v2.variant_in_roles
    assert 'dad1' in v2.variant_in_members


def test_members_in_order1_genotype_full(full_vcf):
    fvars = full_vcf("fixtures/members_in_order1")
    for v in fvars.query_variants():
        print(v, mat2str(v.best_st), mat2str(v.gt), v.inheritance)
        assert 'gpa' in v.variant_in_members
        assert Role.paternal_grandfather in v.variant_in_roles


def test_members_in_order2_genotype_full(full_vcf):
    fvars = full_vcf("fixtures/members_in_order2")
    for v in fvars.query_variants():
        print(v, mat2str(v.best_st), mat2str(v.gt), v.inheritance)
        assert 'gpa' in v.variant_in_members
        assert Role.paternal_grandfather in v.variant_in_roles


def test_freq_trios_2_full(full_vcf):
    fvars = full_vcf("fixtures/trios2")
    vs = list(fvars.query_variants(
        family_ids=['f1'], regions=[Region("1", 11539, 11540)]))
    assert len(vs) == 2

    v1 = vs[0]
    v2 = vs[1]

    print(v1, mat2str(v1.best_st), mat2str(v1.gt), v1.inheritance)
    assert v1.get_attr('all.nAltAlls')[1] == 2
    assert v1.get_attr('all.altFreq')[1] == 25

    assert Role.mom in v1.variant_in_roles
    assert 'mom1' in v1.variant_in_members

    print(v2, mat2str(v2.best_st), mat2str(v2.gt), v2.inheritance)
    assert v1.get_attr('all.nAltAlls')[1] == 2
    assert v1.get_attr('all.altFreq')[1] == 25
    assert Role.dad in v2.variant_in_roles
    assert 'dad1' in v2.variant_in_members
