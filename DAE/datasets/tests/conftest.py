'''
Created on Feb 6, 2017

@author: lubo
'''
import pytest
from datasets.config import DatasetsConfig
from datasets.dataset import Dataset


@pytest.fixture(scope='session')
def datasets_config(request):
    return DatasetsConfig()


@pytest.fixture(scope='session')
def ssc(request, datasets_config):
    desc = datasets_config.get_dataset('SSC')
    dataset = Dataset(desc)
    return dataset


@pytest.fixture(scope='session')
def vip(request, datasets_config):
    desc = datasets_config.get_dataset('VIP')
    dataset = Dataset(desc)
    return dataset


@pytest.fixture(scope='session')
def sd(request, datasets_config):
    desc = datasets_config.get_dataset('SD')
    dataset = Dataset(desc)
    return dataset
