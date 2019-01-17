'''
Created on Mar 29, 2018

@author: lubo
'''
from __future__ import unicode_literals
import os
import shutil

import pytest

from gene.config import GeneInfoConfig
from gene.gene_set_collections import GeneSetsCollections
from studies.study_definition import SingleFileStudiesDefinition
from study_groups.study_group_definition import \
    SingleFileStudiesGroupDefinition
from utils.fixtures import path_to_fixtures as _path_to_fixtures
# Used by pytest
from study_groups.tests.conftest import study_group_facade, \
    study_groups_factory
from configurable_entities.configuration import DAEConfig


def path_to_fixtures(*args):
    return _path_to_fixtures('gene', *args)


def mock_property(mocker):
    def result(property, mock_value):
        file_mock = mocker.patch(property, new_callable=mocker.PropertyMock)
        file_mock.return_value = mock_value
    return result


@pytest.fixture(scope='session')
def studies_definition():
    return SingleFileStudiesDefinition(
        path_to_fixtures('studies', 'studies.conf'),
        path_to_fixtures('studies'))


@pytest.fixture(scope='session')
def basic_study_groups_definition():
    return SingleFileStudiesGroupDefinition(
        path_to_fixtures('studies', 'study_group.conf'))


@pytest.fixture()
def mocked_dataset_config(mocker):
    mp = mock_property(mocker)

    mp(
        'configurable_entities.configuration.DAEConfig.gene_info_conf',
        path_to_fixtures('gene_info.conf'))
    mp(
        'configurable_entities.configuration.DAEConfig.gene_info_dir',
        path_to_fixtures())
    # mp(
    #     'configurable_entities.configuration.DAEConfig.dae_data_dir',
    #     path_to_fixtures())

    return DAEConfig()


@pytest.fixture()
def gene_info_config(mocked_dataset_config):
    return GeneInfoConfig(config=mocked_dataset_config)


@pytest.fixture
def gscs(study_group_facade, gene_info_config):
    return GeneSetsCollections(
        study_group_facade=study_group_facade, config=gene_info_config)


@pytest.fixture(scope='module')
def gene_info_cache_dir():
    cache_dir = path_to_fixtures('geneInfo', 'cache')
    assert not os.path.exists(cache_dir), \
        'Cache dir "{}"already  exists..'.format(cache_dir)
    os.makedirs(cache_dir)

    env_key = 'DATA_STUDY_GROUPS_DENOVO_GENE_SETS_DIR'
    old_env = os.getenv(env_key, None)

    os.environ[env_key] = \
        path_to_fixtures('geneInfo', 'cache')

    yield

    shutil.rmtree(cache_dir)

    if old_env is None:
        os.unsetenv(env_key)
    else:
        os.putenv(env_key, old_env)


@pytest.fixture()
def calc_gene_sets(gscs):
    denovo_gene_sets = gscs.get_gene_sets_collection('denovo', load=False)

    denovo_gene_sets.load(build_cache=True)

    print("PRECALCULATION COMPLETE")
