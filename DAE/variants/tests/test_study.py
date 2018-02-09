'''
Created on Feb 9, 2018

@author: lubo
'''
from RegionOperations import Region


def test_study_load(uagre_study):

    assert uagre_study.vars_df is not None
    assert uagre_study.vcf_vars is not None

    assert len(uagre_study.vars_df) == len(uagre_study.vcf_vars)


def test_study_query_regions(uagre_study):
    df = uagre_study.query_regions([Region("1", 11541, 11541)])
    assert df is not None
    assert len(df) == 1


def test_study_query_regions_2(uagre_study):
    regions = [
        Region("1", 11541, 11541),
        Region("1", 54711, 54721)
    ]
    df = uagre_study.query_regions(regions)
    assert df is not None
    assert len(df) == 3


def test_query_genes(uagre_study):
    genes = ['FAM87B']
    df = uagre_study.query_genes(genes)
    assert df is not None
    assert len(df) == 6


def test_query_effect_types(uagre_study):
    df = uagre_study.query_effect_types(['frame-shift'])
    assert len(df) == 2


def test_query_genes_and_effect_types(uagre_study):
    genes = ['KIAA1751']
    effect_types = ['frame-shift']
    df = uagre_study.query_genes_effect_types(effect_types, genes)
    assert len(df) == 2

    df = uagre_study.query_genes_effect_types(None, genes)
    assert len(df) == 205

    df = uagre_study.query_genes_effect_types(
        ['frame-shift', 'missense'], genes)
    assert len(df) == 4

    df = uagre_study.query_genes_effect_types(
        ['frame-shift', 'missense', 'synonymous'], genes)
    assert len(df) == 7


def test_query_genes_3(uagre_study):
    genes = ['FAM87B', 'SAMD11', 'NOC2L']
    df = uagre_study.query_genes(genes)
    assert df is not None

    assert len(df) == 81
