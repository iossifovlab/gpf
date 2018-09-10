'''
Created on Feb 9, 2018

@author: lubo
'''
from __future__ import print_function

from RegionOperations import Region
import pytest


@pytest.mark.xfail
def test_study_load(ustudy_vcf):

    assert ustudy_vcf.annot_df is not None
    assert ustudy_vcf.vcf_vars is not None

    assert len(ustudy_vcf.annot_df.groupby("summary_variant_index")) == \
        len(ustudy_vcf.vcf_vars)


@pytest.mark.xfail
def test_query_regions(ustudy_vcf):
    regions = [Region("1", 11539, 11541)]
    vs = ustudy_vcf.query_variants(regions=regions)
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 1


@pytest.mark.xfail
def test_query_regions_2(ustudy_vcf):
    regions = [
        Region("1", 11539, 11541),
        Region("1", 54709, 54721)
    ]
    vs = ustudy_vcf.query_variants(regions=regions)
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 3


# FIXME:
# def test_query_genes(ustudy_vcf):
#     genes = ['FAM87B']
#     vs = ustudy_vcf.query_variants(genes=genes)
#     assert vs is not None
#     vl = list(vs)
#     assert len(vl) == 7


# FIXME:
# def test_query_effect_types(ustudy_vcf):
#     effect_types = ['missense']
#     vs = ustudy_vcf.query_variants(effect_types=effect_types)
#     assert vs is not None
#     vl = list(vs)
#     for v in vl:
#         print(v, mat2str(v.best_st), v.effects)
#     # FIXME: review and add more detailed tests for variant 1:877831
#     # FIXME: got one bonus variant:
#     # 1:877831 T->C,GC AU1921 0000?000?/2222?222?
#     # [missense:[SAMD11:missense], frame-shift:[SAMD11:frame-shift]]
#     # assert len(vl) == 4
#     assert len(vl) == 3
#
#
# def test_query_genes_and_effect_types(ustudy_vcf):
#     genes = ['NOC2L']
#     effect_types = ['missense']
#     vs = ustudy_vcf.query_variants(effect_types=effect_types, genes=genes)
#     assert vs is not None
#     vl = list(vs)
#     assert len(vl) == 2
#
#     vs = ustudy_vcf.query_variants(genes=genes)
#     assert vs is not None
#     vl = list(vs)
#     assert len(vl) == 44
#
#     vs = ustudy_vcf.query_variants(
#         effect_types=['frame-shift', 'missense'], genes=genes)
#     assert vs is not None
#     vl = list(vs)
#     assert len(vl) == 2
#
#     vs = ustudy_vcf.query_variants(
#         effect_types=['missense', 'synonymous'], genes=genes)
#     assert vs is not None
#     vl = list(vs)
#     assert len(vl) == 5
#
#
# def test_query_genes_3(ustudy_vcf):
#     genes = ['FAM87B', 'SAMD11', 'NOC2L']
#     vs = ustudy_vcf.query_variants(genes=genes)
#     assert vs is not None
#     vl = list(vs)
#     assert len(vl) == 113
#
#
# def test_query_persons(ustudy_vcf):
#     genes = ['NOC2L']
#     effect_types = ['missense']
#
#     vs = ustudy_vcf.query_variants(
#         genes=genes, effect_types=effect_types,
#         person_ids=['AU1921202'])
#     assert vs is not None
#     vl = list(vs)
#     assert len(vl) == 2
#
#     vs = ustudy_vcf.query_variants(
#         genes=genes, effect_types=effect_types,
#         person_ids=['AU1921202', 'AU1921211'])
#     assert vs is not None
#     vl = list(vs)
#     assert len(vl) == 2
#
#
# def test_query_persons_all(ustudy_vcf):
#     vs = ustudy_vcf.query_variants(
#         person_ids=['AU1921202'])
#     assert vs is not None
#     vl = list(vs)
#     assert len(vl) == 361
#
#     vs = ustudy_vcf.query_variants(
#         person_ids=['AU1921202', 'AU1921211'])
#     assert len(list(vs)) == 435
#
#
# def test_query_persons_combined(ustudy_vcf):
#     genes = ['NOC2L']
#     effect_types = ['missense']
#     vs = ustudy_vcf.query_variants(
#         genes=genes, effect_types=effect_types,
#         person_ids=['AU1921202'])
#     assert vs is not None
#     vl = list(vs)
#     assert len(vl) == 2
#
#     vs = ustudy_vcf.query_variants(
#         genes=genes, effect_types=effect_types,
#         person_ids=['AU1921201', 'AU1921305'])
#     assert vs is not None
#     vl = list(vs)
#     assert len(vl) == 1
#
#
# def test_query_families(ustudy_vcf):
#     genes = ['NOC2L']
#     effect_types = ['missense']
#     family_ids = ['AU1921']
#     vs = ustudy_vcf.query_variants(
#         genes=genes,
#         effect_types=effect_types,
#         family_ids=family_ids)
#     assert vs is not None
#     vl = list(vs)
#     assert len(vl) == 2
#
#
# def test_query_families_0(ustudy_vcf):
#     genes = ['NOC2L']
#     effect_types = ['missense']
#     family_ids = ['wrong_family_id']
#     vs = ustudy_vcf.query_variants(
#         genes=genes,
#         effect_types=effect_types,
#         family_ids=family_ids)
#     assert vs is not None
#     vl = list(vs)
#     assert len(vl) == 0
#
#
# def test_query_variants_single(ustudy_vcf):
#     vs = ustudy_vcf.query_variants(
#         regions=[Region("1", 11540, 11541)])
#     for v in vs:
#         print(v, "mendelian: ", v.is_mendelian())
#         print(v.gt)
#         print(v.best_st)
#         assert v.is_mendelian()
#
#
# def test_query_variants_persons_all(ustudy_vcf):
#     vs = ustudy_vcf.query_variants(
#         genes=['FAM87B'],
#         person_ids=['AU1921202'])
#     for v in vs:
#         print(v, "mendelian: ", v.is_mendelian())
#         print(v.gt)
#         print(v.best_st)
#
#
# def test_query_variants_roles_dad(ustudy_vcf):
#     genes = ['NOC2L']
#     role_query = "dad"
#
#     vs = ustudy_vcf.query_variants(
#         genes=genes,
#         roles=role_query
#     )
#
#     for v in vs:
#         print(v, "mendelian: ", v.is_mendelian())
#         print(v.gt)
#         print(v.best_st)
