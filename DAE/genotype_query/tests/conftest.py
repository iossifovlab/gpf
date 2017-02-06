'''
Created on Feb 6, 2017

@author: lubo
'''
import pytest
from datasets.config import DatasetsConfig
from genotype_query.query import QueryDataset


@pytest.fixture(scope='session')
def datasets(request):
    datasets_config = DatasetsConfig()
    return datasets_config.get_datasets()


@pytest.fixture(scope='session')
def query(request, datasets):
    query = QueryDataset(datasets)
    return query
