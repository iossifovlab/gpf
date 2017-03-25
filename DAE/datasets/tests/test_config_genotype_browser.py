'''
Created on Mar 21, 2017

@author: lubo
'''
from pprint import pprint


def test_vip_pheno_columns(datasets_config):
    vip = datasets_config.get_dataset_desc('VIP')
    section = 'dataset.{}'.format('VIP')

    res = datasets_config._get_genotype_browser_pheno_columns(section)
    pprint(res)

    # pprint(vip)
    pheno_columns = vip['genotypeBrowser']['phenoColumns']
    assert pheno_columns is not None
    pprint(pheno_columns)

    assert 'name' in pheno_columns[0]
    assert 'slots' in pheno_columns[0]


def test_ssc_pheno_filters(datasets_config):
    ssc = datasets_config.get_dataset_desc('SSC')

    pheno_filters = ssc['genotypeBrowser']['phenoFilters']
    assert pheno_filters is not None
    pprint(pheno_filters)

    assert 'name' in pheno_filters[0]
    assert 'measure_type' in pheno_filters[0]
    assert 'measure_filter' in pheno_filters[0]


def test_vip_pheno_filters(datasets_config):
    ssc = datasets_config.get_dataset_desc('VIP')

    pheno_filters = ssc['genotypeBrowser']['phenoFilters']
    assert pheno_filters is not None
    pprint(pheno_filters)

    assert 'name' in pheno_filters[0]
    assert 'measure_type' in pheno_filters[0]
    assert 'measure_filter' in pheno_filters[0]
