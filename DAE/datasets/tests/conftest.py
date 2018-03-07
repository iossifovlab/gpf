'''
Created on Feb 6, 2017

@author: lubo
'''
import pytest
from datasets.config import DatasetsConfig
from datasets.datasets_factory import DatasetsFactory

import DAE


@pytest.fixture(scope='session')
def datasets_config(request):
    return DatasetsConfig()


@pytest.fixture(scope='session')
def datasets_factory(request, datasets_config):
    return DatasetsFactory(datasets_config)


@pytest.fixture(scope='session')
def ssc(request, datasets_factory):
    return datasets_factory.get_dataset('SSC')


@pytest.fixture(scope='session')
def vip(request,  datasets_factory):
    return datasets_factory.get_dataset('VIP')


@pytest.fixture(scope='session')
def sd(request,  datasets_factory):
    return datasets_factory.get_dataset('SD')


@pytest.fixture(scope='session')
def denovodb(request,  datasets_factory):
    return datasets_factory.get_dataset('denovo_db')


@pytest.fixture(scope='session')
def ssc_pheno(request):
    pf = DAE.pheno
    db = pf.get_pheno_db('ssc')
    return db


@pytest.fixture(scope='session')
def vip_pheno():
    pf = DAE.pheno
    db = pf.get_pheno_db('vip')
    return db


@pytest.fixture(scope='session')
def spark(request,  datasets_factory):
    return datasets_factory.get_dataset('SPARK')


@pytest.fixture(scope='session')
def agre(request,  datasets_factory):
    return datasets_factory.get_dataset('AGRE_WG')

