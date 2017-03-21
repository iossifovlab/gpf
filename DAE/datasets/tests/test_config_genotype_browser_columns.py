'''
Created on Mar 21, 2017

@author: lubo
'''


def test_vip_pheno_columns(datasets_config):
    vip = datasets_config.get_dataset_desc('VIP')
    section = 'dataset.{}'.format('VIP')

    res = datasets_config._get_genotype_browser_pheno_columns(section)
    print(res)
