'''
Created on Feb 7, 2018

@author: lubo
'''
import pytest

from variants.configure import Configure
from variants.loader import RawVariantsLoader
from variants.raw_vcf import RawFamilyVariants


@pytest.fixture(scope='session')
def uagre_config():
    config = Configure.from_config()
    return config


@pytest.fixture(scope='session')
def uagre_loader(uagre_config):
    return RawVariantsLoader(uagre_config)


@pytest.fixture(scope='session')
def uagre(uagre_config):
    fvariants = RawFamilyVariants(uagre_config)
    return fvariants
