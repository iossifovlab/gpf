'''
Created on Mar 29, 2018

@author: lubo
'''
import pytest

from Config import Config
from gene.config import GeneInfoConfig
from gene.gene_set_collections import GeneSetsCollections
from studies.study_definition import SingleFileStudiesDefinition
from study_groups.study_group_definition import SingleFileStudiesGroupDefinition
from utils.fixtures import path_to_fixtures as _path_to_fixtures
# Used by pytest
from study_groups.tests.conftest import study_group_facade, study_groups_factory


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
def basic_groups_definition():
    return SingleFileStudiesGroupDefinition(
        path_to_fixtures('studies', 'study_group.conf'))


@pytest.fixture()
def mocked_dataset_config(mocker):
    mp = mock_property(mocker)

    mp('Config.Config.geneInfoDBconfFile', path_to_fixtures('gene_info.conf'))
    mp('Config.Config.geneInfoDBdir', path_to_fixtures())
    mp('Config.Config.daeDir', path_to_fixtures())

    return Config()


@pytest.fixture()
def gene_info_config(mocked_dataset_config):
    return GeneInfoConfig(config=mocked_dataset_config)


@pytest.fixture()
def gscs(study_group_facade, gene_info_config):
    res = GeneSetsCollections(
        study_group_facade=study_group_facade, config=gene_info_config)
    return res
