'''
Created on Feb 7, 2018

@author: lubo
'''
from variants.configure import Configure
from variants.loader import StudyLoader
import pytest


@pytest.fixture(scope='session')
def uagre_loader():
    config = Configure.from_file()
    return StudyLoader(config['study.uagre'])
