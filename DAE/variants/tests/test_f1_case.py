'''
Created on Jul 12, 2018

@author: lubo
'''
from __future__ import print_function

from variants.vcf_utils import mat2str
from variants.attributes_query import inheritance_query
from variants.attributes import Inheritance
import pytest
from RegionOperations import Region


@pytest.mark.parametrize("regions,inheritance,effect_types,count", [
    ([Region("1", 878152, 878152)], None, None, 1),
    ([Region("1", 878152, 878152)], "denovo", ["synonymous"], 0),
    ([Region("1", 878152, 878152)], "denovo", ["missense"], 1),
    ([Region("1", 878152, 878152)], "mendelian", ["synonymous"], 1),
    ([Region("1", 878152, 878152)], "mendelian", ["missense"], 0),
])
def test_f1_simple(variants_vcf, regions, inheritance, effect_types, count):

    vvars = variants_vcf("fixtures/f1_test")
    assert vvars is not None

    vs = vvars.query_variants(
        regions=regions,
        inheritance=inheritance,
        effect_types=effect_types)
    vs = list(vs)
    for v in vs:
        print(
            v, v.inheritance,
            v.effects, mat2str(v.best_st))
        for aa in v.alt_alleles:
            print(
                aa, aa.effect,
                aa.inheritance_in_members,
                mat2str(aa.gt),
                mat2str(aa.best_st))
        break
    assert len(vs) == count


@pytest.mark.parametrize("query,positive,negative", [
    ("denovo",
     [Inheritance.denovo],
     [Inheritance.omission]),
    ("denovo",
     [Inheritance.denovo, Inheritance.omission],
     [Inheritance.omission, Inheritance.mendelian]),
    ("denovo or omission",
     [Inheritance.denovo],
     [Inheritance.mendelian]),
    ("denovo or omission",
     [Inheritance.denovo, Inheritance.unknown],
     [Inheritance.mendelian, Inheritance.unknown]),
    ("not denovo and not omission",
     [Inheritance.mendelian, Inheritance.unknown],
     [Inheritance.denovo, Inheritance.unknown]),
])
def test_f1_inheritance_query(query, positive, negative):
    query = inheritance_query.\
        transform_tree_to_matcher(
            inheritance_query.transform_query_string_to_tree(query))
    assert query.match(positive)
    assert not query.match(negative)


@pytest.mark.parametrize("regions,inheritance,effect_types,count", [
    ([Region("1", 901923, 901923)], None, None, 1),
    ([Region("1", 901923, 901923)], "unknown", None, 1),
    ([Region("1", 901923, 901923)], "mendelian", None, 0),
])
def test_f1_all_unknown(
        variants_vcf, regions, inheritance, effect_types, count):

    # vvars = variants_vcf("fixtures/effects_trio_multi")
    vvars = variants_vcf("fixtures/f1_test")
    assert vvars is not None

    vs = vvars.query_variants(
        regions=regions,
        inheritance=inheritance,
        effect_types=effect_types)
    vs = list(vs)
    for v in vs:
        print(
            v, v.inheritance,
            v.effects, mat2str(v.best_st))
        for aa in v.alleles:
            print(
                aa, aa.effect,
                aa.inheritance_in_members,
                mat2str(aa.gt),
                mat2str(aa.best_st))
        break
    assert len(vs) == count


@pytest.mark.parametrize("regions,inheritance,effect_types,count", [
    ([Region("1", 905951, 905951)], None, None, 1),
    ([Region("1", 905951, 905951)], "unknown", None, 1),
    ([Region("1", 905951, 905951)], "mendelian", None, 1),
])
def test_f1_unknown_and_reference(
        variants_vcf, regions, inheritance, effect_types, count):

    # vvars = variants_vcf("fixtures/effects_trio_multi")
    vvars = variants_vcf("fixtures/f1_test")
    assert vvars is not None

    vs = vvars.query_variants(
        regions=regions,
        inheritance=inheritance,
        effect_types=effect_types)
    vs = list(vs)
    for v in vs:
        print(
            v, v.inheritance,
            v.effects, mat2str(v.best_st))
        for aa in v.alleles:
            print(
                aa, aa.effect,
                aa.inheritance_in_members,
                mat2str(aa.gt),
                mat2str(aa.best_st))
        break
    assert len(vs) == count


@pytest.mark.parametrize("regions,inheritance,effect_types,count", [
    ([Region("1", 905957, 905957)], None, None, 1),
    ([Region("1", 905957, 905957)], "unknown", None, 1),
    ([Region("1", 905957, 905957)], "mendelian", None, 1),
    ([Region("1", 905957, 905957)], "mendelian", ["synonymous"], 0),
    ([Region("1", 905957, 905957)], "mendelian", ["missense"], 0),
    ([Region("1", 905957, 905957)], "denovo", ["synonymous"], 1),
    ([Region("1", 905957, 905957)], "denovo", ["missense"], 0),
])
def test_f1_cannonical_denovo(
        variants_vcf, regions, inheritance, effect_types, count):

    # vvars = variants_vcf("fixtures/effects_trio_multi")
    vvars = variants_vcf("fixtures/f1_test")
    assert vvars is not None

    vs = vvars.query_variants(
        regions=regions,
        inheritance=inheritance,
        effect_types=effect_types)
    vs = list(vs)
    for v in vs:
        print(
            v, v.inheritance,
            v.effects, mat2str(v.best_st))
        for aa in v.alleles:
            print(
                aa, aa.effect,
                aa.inheritance_in_members,
                mat2str(aa.gt),
                mat2str(aa.best_st))
        break
    assert len(vs) == count
