'''
Created on Feb 9, 2018

@author: lubo
'''
from __future__ import print_function

from RegionOperations import Region
from variants.roles import Role, RoleQuery


def test_study_load(uagre):

    assert uagre.vars_df is not None
    assert uagre.vcf_vars is not None

    assert len(uagre.vars_df) == len(uagre.vcf_vars)


def test_query_regions(uagre):
    regions = [Region("1", 11540, 11541)]
    vs = uagre.query_variants(regions=regions)
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 1


def test_query_regions_2(uagre):
    regions = [
        Region("1", 11540, 11541),
        Region("1", 54710, 54721)
    ]
    vs = uagre.query_variants(regions=regions)
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 3


def test_query_genes(uagre):
    genes = ['FAM87B']
    vs = uagre.query_variants(genes=genes)
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 7


def test_query_effect_types(uagre):
    effect_types = ['frame-shift']
    vs = uagre.query_variants(effect_types=effect_types)
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 2


def test_query_genes_and_effect_types(uagre):
    genes = ['KIAA1751']
    effect_types = ['frame-shift']
    vs = uagre.query_variants(effect_types=effect_types, genes=genes)
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 2

    vs = uagre.query_variants(genes=genes)
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 227

    vs = uagre.query_variants(
        effect_types=['frame-shift', 'missense'], genes=genes)
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 4

    vs = uagre.query_variants(
        effect_types=['frame-shift', 'missense', 'synonymous'], genes=genes)
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 7


def test_query_genes_3(uagre):
    genes = ['FAM87B', 'SAMD11', 'NOC2L']
    vs = uagre.query_variants(genes=genes)
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 112


def test_query_persons(uagre):
    genes = ['KIAA1751']
    effect_types = ['frame-shift']

    vs = uagre.query_variants(
        genes=genes, effect_types=effect_types,
        person_ids=['AU1921202'])
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 2

    vs = uagre.query_variants(
        genes=genes, effect_types=effect_types,
        person_ids=['AU1921202', 'AU1921211'])
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 2


def test_query_persons_all(uagre):
    vs = uagre.query_variants(
        person_ids=['AU1921202'])
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 15977

    vs = uagre.query_variants(
        person_ids=['AU1921202', 'AU1921211'])
    assert len(list(vs)) == 21299


def test_query_persons_combined(uagre):
    genes = ['KIAA1751']
    effect_types = ['frame-shift']
    vs = uagre.query_variants(
        genes=genes, effect_types=effect_types,
        person_ids=['AU1921202'])
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 2

    vs = uagre.query_variants(
        genes=genes, effect_types=effect_types,
        person_ids=['AU1921201', 'AU1921305'])
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 0


# def test_query_families(uagre):
#     genes = ['KIAA1751']
#     effect_types = ['frame-shift']
#     df = uagre.query_genes_effect_types(effect_types, genes, uagre.vars_df)
#
#     vs = uagre.query_families(['AU1921'], df)
#     assert len(list(vs)) == 2
#
#
# def test_query_variants_single(uagre):
#     vs = uagre.query_variants(
#         regions=[Region("1", 11541, 11541)])
#     for v in vs:
#         print(v, "Medelian: ", v.is_medelian())
#         print(v.gt)
#         print(v.best_st)
#
#
# def test_query_variants_persons_all(uagre):
#     vs = uagre.query_variants(
#         genes=['FAM87B'],
#         person_ids=['AU1921202'])
#     for v in vs:
#         print(v, "Medelian: ", v.is_medelian())
#         print(v.gt)
#         print(v.best_st)
#
#
# def test_query_variants_roles_dad(uagre):
#     genes = ['KIAA1751']
#     role_query = RoleQuery(Role.dad)
#
#     vs = uagre.query_variants(
#         genes=genes,
#         roles=[role_query]
#     )
#
#     for v in vs:
#         print(v, "Medelian: ", v.is_medelian())
#         print(v.gt)
#         print(v.best_st)
