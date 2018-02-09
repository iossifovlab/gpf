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
    df = uagre_study.query_regions(Region("1", 11541, 11541))
    assert df is not None
    assert len(df) == 1

    print(df)


def test_study_query_regions_2(uagre_study):
    regions = [
        Region("1", 11541, 11541),
        Region("1", 54711, 54721)
    ]
    df = uagre_study.query_regions(*regions)
    assert df is not None
    assert len(df) == 3

    print(df)


def test_query_genes(uagre_study):
    genes = ['FAM87B']
    df = uagre_study.query_genes(*genes)
    assert df is not None

    print(df)


# def test_query_genes_3(uagre_study):
#     genes = ['FAM87B', 'SAMD11', 'NOC2L']
#     df = uagre_study.query_genes(*genes)
#     assert df is not None
#
#     print(df)
#     print(len(df))
