'''
Created on Aug 23, 2016

@author: lubo
'''
from pheno_db.utils.configuration import PhenoConfig


def test_pheno_config_create():
    config = PhenoConfig()
    assert config is not None
