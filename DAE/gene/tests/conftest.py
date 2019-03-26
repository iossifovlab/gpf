'''
Created on Mar 29, 2018

@author: lubo
'''
from __future__ import unicode_literals
import os
import shutil

import pytest

from utils.fixtures import change_environment

from gene.config import GeneInfoConfig
from gene.gene_set_collections import GeneSetsCollections
from gene.weights import WeightsLoader

from utils.fixtures import path_to_fixtures as _path_to_fixtures
# Used by pytest
from configurable_entities.configuration import DAEConfig
from studies.factory import VariantsDb


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


def path_to_fixtures(*args):
    return _path_to_fixtures('gene', *args)


def mock_property(mocker):
    def result(property, mock_value):
        file_mock = mocker.patch(property, new_callable=mocker.PropertyMock)
        file_mock.return_value = mock_value
    return result


@pytest.fixture()
def gene_info_config(dae_config_fixture):
    return GeneInfoConfig(dae_config_fixture)


@pytest.fixture  # noqa
def gscs(variants_db_fixture, gene_info_config):
    return GeneSetsCollections(
        variants_db=variants_db_fixture, config=gene_info_config)


@pytest.fixture(scope='module')
def gene_info_cache_dir():
    cache_dir = path_to_fixtures('geneInfo', 'cache')
    assert not os.path.exists(cache_dir), \
        'Cache dir "{}"already  exists..'.format(cache_dir)
    os.makedirs(cache_dir)

    new_envs = {
        'DATA_STUDY_GROUPS_DENOVO_GENE_SETS_DIR':
            path_to_fixtures('geneInfo', 'cache'),
        'DAE_DB_DIR':
            path_to_fixtures()
    }

    for val in change_environment(new_envs):
        yield val

    shutil.rmtree(cache_dir)


@pytest.fixture()
def calc_gene_sets(gscs):
    denovo_gene_sets = gscs.get_gene_sets_collection('denovo', load=False)

    denovo_gene_sets.load(build_cache=True)

    print("PRECALCULATION COMPLETE")


@pytest.fixture()
def weights_loader(gene_info_config):
    return WeightsLoader(config=gene_info_config)


@pytest.fixture(scope='session')
def dae_config_fixture():
    dae_config = DAEConfig(fixtures_dir())
    return dae_config


@pytest.fixture(scope='session')
def variants_db_fixture(dae_config_fixture):
    vdb = VariantsDb(dae_config_fixture)
    return vdb
