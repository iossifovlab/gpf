'''
Created on Feb 9, 2018

@author: lubo
'''
from __future__ import print_function

from RegionOperations import Region
from variants.attributes import Role, RoleQuery


def test_study_load(ustudy):

    assert ustudy.annot_df is not None
    assert ustudy.vcf_vars is not None

    assert len(ustudy.annot_df) == len(ustudy.vcf_vars)


def test_query_regions(ustudy):
    regions = [Region("1", 11539, 11541)]
    vs = ustudy.query_variants(regions=regions)
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 1


def test_query_regions_2(ustudy):
    regions = [
        Region("1", 11539, 11541),
        Region("1", 54709, 54721)
    ]
    vs = ustudy.query_variants(regions=regions)
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 3


def test_query_genes(ustudy):
    genes = ['FAM87B']
    vs = ustudy.query_variants(genes=genes)
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 7


def test_query_effect_types(ustudy):
    effect_types = ['missense']
    vs = ustudy.query_variants(effect_types=effect_types)
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 3


def test_query_genes_and_effect_types(ustudy):
    genes = ['NOC2L']
    effect_types = ['missense']
    vs = ustudy.query_variants(effect_types=effect_types, genes=genes)
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 1

    vs = ustudy.query_variants(genes=genes)
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 44

    vs = ustudy.query_variants(
        effect_types=['frame-shift', 'missense'], genes=genes)
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 1

    vs = ustudy.query_variants(
        effect_types=['missense', 'synonymous'], genes=genes)
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 5


def test_query_genes_3(ustudy):
    genes = ['FAM87B', 'SAMD11', 'NOC2L']
    vs = ustudy.query_variants(genes=genes)
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 113


def test_query_persons(ustudy):
    genes = ['NOC2L']
    effect_types = ['missense']

    vs = ustudy.query_variants(
        genes=genes, effect_types=effect_types,
        person_ids=['AU1921202'])
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 1

    vs = ustudy.query_variants(
        genes=genes, effect_types=effect_types,
        person_ids=['AU1921202', 'AU1921211'])
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 1


def test_query_persons_all(ustudy):
    vs = ustudy.query_variants(
        person_ids=['AU1921202'])
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 362

    vs = ustudy.query_variants(
        person_ids=['AU1921202', 'AU1921211'])
    assert len(list(vs)) == 436


def test_query_persons_combined(ustudy):
    genes = ['NOC2L']
    effect_types = ['missense']
    vs = ustudy.query_variants(
        genes=genes, effect_types=effect_types,
        person_ids=['AU1921202'])
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 1

    vs = ustudy.query_variants(
        genes=genes, effect_types=effect_types,
        person_ids=['AU1921201', 'AU1921305'])
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 1


def test_query_families(ustudy):
    genes = ['NOC2L']
    effect_types = ['missense']
    family_ids = ['AU1921']
    vs = ustudy.query_variants(
        genes=genes,
        effect_types=effect_types,
        family_ids=family_ids)
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 1


def test_query_families_0(ustudy):
    genes = ['NOC2L']
    effect_types = ['missense']
    family_ids = ['wrong_family_id']
    vs = ustudy.query_variants(
        genes=genes,
        effect_types=effect_types,
        family_ids=family_ids)
    assert vs is not None
    vl = list(vs)
    assert len(vl) == 0


def test_query_variants_single(ustudy):
    vs = ustudy.query_variants(
        regions=[Region("1", 11540, 11541)])
    for v in vs:
        print(v, "mendelian: ", v.is_mendelian())
        print(v.gt)
        print(v.best_st)
        assert v.is_mendelian()


def test_query_variants_persons_all(ustudy):
    vs = ustudy.query_variants(
        genes=['FAM87B'],
        person_ids=['AU1921202'])
    for v in vs:
        print(v, "mendelian: ", v.is_mendelian())
        print(v.gt)
        print(v.best_st)


def test_query_variants_roles_dad(ustudy):
    genes = ['NOC2L']
    role_query = RoleQuery.any_of(Role.dad)

    vs = ustudy.query_variants(
        genes=genes,
        roles=role_query
    )

    for v in vs:
        print(v, "mendelian: ", v.is_mendelian())
        print(v.gt)
        print(v.best_st)
