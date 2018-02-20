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
    df = uagre.query_regions([Region("1", 11540, 11541)], uagre.vars_df)
    assert df is not None
    assert len(df) == 1


def test_query_regions_2(uagre):
    regions = [
        Region("1", 11540, 11541),
        Region("1", 54710, 54721)
    ]
    df = uagre.query_regions(regions, uagre.vars_df)
    assert df is not None
    assert len(df) == 3


def test_query_genes(uagre):
    genes = ['FAM87B']
    df = uagre.query_genes(genes, uagre.vars_df)
    assert df is not None
    assert len(df) == 7


def test_query_effect_types(uagre):
    # print(uagre.vars_df['effectGene'])

    df = uagre.query_effect_types(['frame-shift'], uagre.vars_df)
    assert len(df) == 2


def test_query_genes_and_effect_types(uagre):
    genes = ['KIAA1751']
    effect_types = ['frame-shift']
    df = uagre.query_genes_effect_types(effect_types, genes, uagre.vars_df)
    assert len(df) == 2

    df = uagre.query_genes_effect_types(None, genes, uagre.vars_df)
    assert len(df) == 227

    df = uagre.query_genes_effect_types(
        ['frame-shift', 'missense'], genes, uagre.vars_df)
    assert len(df) == 4

    df = uagre.query_genes_effect_types(
        ['frame-shift', 'missense', 'synonymous'], genes, uagre.vars_df)
    assert len(df) == 7


def test_query_genes_3(uagre):
    genes = ['FAM87B', 'SAMD11', 'NOC2L']
    df = uagre.query_genes(genes, uagre.vars_df)
    assert df is not None

    assert len(df) == 114


def test_query_persons(uagre):
    genes = ['KIAA1751']
    effect_types = ['frame-shift']
    df = uagre.query_genes_effect_types(effect_types, genes, uagre.vars_df)

    vs = uagre.query_persons(['AU1921202'], df)
    assert len(list(vs)) == 2

    vs = uagre.query_persons(
        ['AU1921202', 'AU1921211'], df)
    assert len(list(vs)) == 2


def test_query_persons_all(uagre):

    vs = uagre.query_persons(['AU1921202'], uagre.vars_df)
    assert len(list(vs)) == 15977

    vs = uagre.query_persons(
        ['AU1921202', 'AU1921211'], uagre.vars_df)
    assert len(list(vs)) == 21299


def test_query_persons_missing(uagre):
    genes = ['KIAA1751']
    effect_types = ['frame-shift']
    df = uagre.query_genes_effect_types(effect_types, genes, uagre.vars_df)

    vs = uagre.query_persons(['AU1921201'], df)
    assert len(list(vs)) == 0

    vs = uagre.query_persons(
        ['AU1921201', 'AU1921305'], df)
    assert len(list(vs)) == 0


def test_query_families(uagre):
    genes = ['KIAA1751']
    effect_types = ['frame-shift']
    df = uagre.query_genes_effect_types(effect_types, genes, uagre.vars_df)

    vs = uagre.query_families(['AU1921'], df)
    assert len(list(vs)) == 2


def test_query_variants_single(uagre):
    vs = uagre.query_variants(
        regions=[Region("1", 11541, 11541)])
    for v in vs:
        print(v, "Medelian: ", v.is_medelian())
        print(v.gt)
        print(v.best_st)


def test_query_variants_persons_all(uagre):
    vs = uagre.query_variants(
        genes=['FAM87B'],
        person_ids=['AU1921202'])
    for v in vs:
        print(v, "Medelian: ", v.is_medelian())
        print(v.gt)
        print(v.best_st)


def test_query_variants_roles_dad(uagre):
    genes = ['KIAA1751']
    role_query = RoleQuery(Role.dad)

    vs = uagre.query_variants(
        genes=genes,
        roles=[role_query]
    )

    for v in vs:
        print(v, "Medelian: ", v.is_medelian())
        print(v.gt)
        print(v.best_st)
