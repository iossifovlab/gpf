'''
Created on Nov 23, 2016

@author: lubo
'''
from __future__ import unicode_literals
import pytest

from datasets.config import DatasetsConfig
from datasets.datasets_factory import DatasetsFactory

import DAE


def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true", default=False,
                     help="run slow tests")
    parser.addoption("--runveryslow", action="store_true", default=False,
                     help="run very slow tests")
    parser.addoption("--ssc_wg", action="store_true", default=False,
                     help="run SSC WG tests")
    parser.addoption("--nomysql", action="store_true", default=False,
                     help="skip tests that require mysql")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--runveryslow"):
        # --runveryslow given in cli: do not skip slow tests
        skip_veryslow = pytest.mark.skip(
            reason="need --runveryslow option to run")
        for item in items:
            if "veryslow" in item.keywords:
                item.add_marker(skip_veryslow)

    if not config.getoption("--runslow") and \
            not config.getoption("--runveryslow"):
        # --runslow given in cli: do not skip slow tests
        skip_slow = pytest.mark.skip(
            reason="need --runslow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)

    if config.getoption("--nomysql"):
        skip_mysql = pytest.mark.skip(reason="need mysql data")
        for item in items:
            if "mysql" in item.keywords:
                item.add_marker(skip_mysql)


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
    return datasets_factory.get_dataset('SVIP')


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
