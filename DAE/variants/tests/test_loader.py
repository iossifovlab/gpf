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


def test_load_summary(uagre_loader):
    summary = uagre_loader.load_summary()
    assert summary is not None


def test_load_pedigree(uagre_loader):
    pedigree = uagre_loader.load_pedigree()
    assert pedigree is not None
