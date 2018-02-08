'''
Created on Feb 7, 2018

@author: lubo
'''
from variants.configure import Configure
from variants.loader import StudyLoader
import pytest


@pytest.fixture(scope='session')
def uagre_config():
    config = Configure.from_file()
    return config['study.uagre']


@pytest.fixture(scope='session')
def uagre_loader(uagre_config):
    return StudyLoader(uagre_config)
