'''
Created on Aug 23, 2016

@author: lubo
'''
from pheno_db.utils.load_raw import V15Loader
from pheno_db.precompute.individuals import PrepareIndividuals


def test_v15_loader_default():
    loader = V15Loader()
    dfs = loader.load_table('ssc_core_descriptive')
    assert dfs is not None
    assert len(dfs) == 1
    df = dfs[0]
    assert 'sex' in df.columns


def test_v15_loader_sib():
    loader = V15Loader()
    dfs = loader.load_table('ssc_core_descriptive', roles=['sib'])
    assert dfs is not None
    assert len(dfs) == 2
    df = dfs[0]
    assert 'sex' in df.columns


def test_prepare_individuals():
    prep = PrepareIndividuals()
    assert prep is not None

    df = prep.prepare()
    assert df is not None
    print(df.head())

    prep.cache(df)
