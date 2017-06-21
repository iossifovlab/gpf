'''
Created on Mar 21, 2017

@author: lubo
'''


def test_vip_pheno_columns(datasets_config):
    vip = datasets_config.get_dataset_desc('VIP')

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
    ssc = datasets_config.get_dataset_desc('VIP')

    pheno_filters = ssc['genotypeBrowser']['phenoFilters']
    assert pheno_filters is not None

    assert 'name' in pheno_filters[0]
    assert 'measureType' in pheno_filters[0]
    assert 'measureFilter' in pheno_filters[0]


def test_spark_has_no_genotype_browser(spark):
    print(spark)
    print(dir(spark))

    assert spark.descriptor['genotypeBrowser'] is None
