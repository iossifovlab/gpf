'''
Created on Mar 29, 2018

@author: lubo
'''
from __future__ import unicode_literals
import os
import shutil

import pytest

from studies.study_definition import DirectoryEnabledStudiesDefinition
from studies.study_factory import StudyFactory
from studies.study_facade import StudyFacade
# from studies.study_wrapper import StudyWrapper
from studies.dataset_definition import DirectoryEnabledDatasetsDefinition
from studies.dataset_factory import DatasetFactory
from studies.dataset_facade import DatasetFacade
from utils.fixtures import change_environment

from gene.config import GeneInfoConfig
from gene.gene_set_collections import GeneSetsCollections

from utils.fixtures import path_to_fixtures as _path_to_fixtures
# Used by pytest
from configurable_entities.configuration import DAEConfig


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


def studies_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures/studies'))


def datasets_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures/datasets'))


@pytest.fixture(scope='session')
def study_configs(study_definition):
    return list(study_definition.configs.values())


@pytest.fixture(scope='session')
def study_definitions(dae_config_fixture):
    return DirectoryEnabledStudiesDefinition(
        studies_dir=studies_dir(),
        work_dir=fixtures_dir(),
        default_conf=dae_config_fixture.default_configuration_conf)


@pytest.fixture(scope='session')
def study_factory():
    return StudyFactory()


@pytest.fixture(scope='session')
def study_facade(study_factory, study_definitions):
    return StudyFacade(
        study_factory=study_factory, study_definition=study_definitions)


@pytest.fixture(scope='session')
def dataset_definitions(study_facade, dae_config_fixture):
    return DirectoryEnabledDatasetsDefinition(
        study_facade,
        datasets_dir=datasets_dir(),
        work_dir=fixtures_dir(),
        default_conf=dae_config_fixture.default_configuration_conf)


@pytest.fixture(scope='session')
def dataset_factory(study_facade):
    return DatasetFactory(study_facade=study_facade)


@pytest.fixture(scope='session')
def dataset_facade(dataset_definitions, dataset_factory):
    return DatasetFacade(
        dataset_definitions=dataset_definitions,
        dataset_factory=dataset_factory)


def path_to_fixtures(*args):
    return _path_to_fixtures('gene', *args)


def mock_property(mocker):
    def result(property, mock_value):
        file_mock = mocker.patch(property, new_callable=mocker.PropertyMock)
        file_mock.return_value = mock_value
    return result


@pytest.fixture()
def gene_info_config():
    return GeneInfoConfig()


@pytest.fixture  # noqa
def gscs(dataset_facade, gene_info_config):
    return GeneSetsCollections(
        dataset_facade=dataset_facade, config=gene_info_config)


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


@pytest.fixture(scope='session')
def dae_config_fixture():
    dae_config = DAEConfig(fixtures_dir())
    return dae_config
