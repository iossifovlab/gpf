'''
Created on Mar 21, 2017

@author: lubo
'''
from __future__ import unicode_literals


def test_vip_pheno_columns(datasets_config):
    vip = datasets_config.get_dataset_desc('SVIP')
    pheno_columns = vip['genotypeBrowser']['phenoColumns']
    assert pheno_columns is not None

    assert 'name' in pheno_columns[0]
    assert 'slots' in pheno_columns[0]


def test_ssc_pheno_filters(datasets_config):
    ssc = datasets_config.get_dataset_desc('SSC')

    pheno_filters = ssc['genotypeBrowser']['phenoFilters']
    assert pheno_filters is not None

    assert 'name' in pheno_filters[0]
    assert 'measureType' in pheno_filters[0]
    assert 'measureFilter' in pheno_filters[0]


def test_vip_pheno_filters(datasets_config):
    ssc = datasets_config.get_dataset_desc('SVIP')

    pheno_filters = ssc['genotypeBrowser']['phenoFilters']
    assert pheno_filters is not None

    assert 'name' in pheno_filters[0]
    assert 'measureType' in pheno_filters[0]
    assert 'measureFilter' in pheno_filters[0]


def test_meta_genes_block_show_all_is_false(datasets_config):
    meta = datasets_config.get_dataset_desc('META')
    assert not meta['genotypeBrowser']['genesBlockShowAll']


def test_sd_genes_block_show_all_is_true(datasets_config):
    sd = datasets_config.get_dataset_desc('SD')
    assert sd['genotypeBrowser']['genesBlockShowAll']

