import pytest
import os
import shutil

from DAE import Config
from DAE import GeneInfoConfig
from DAE import GeneSetsCollections
from studies.study_definition import SingleFileStudiesDefinition
from study_groups.study_group_definition import SingleFileStudiesGroupDefinition
# Used by pytest
from study_groups.tests.conftest import study_group_facade, study_groups_factory

from utils.fixtures import path_to_fixtures as _path_to_fixtures


def path_to_fixtures(*args, package='wdae'):
    return _path_to_fixtures('gene_sets', *args, package=package)


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

    print(path_to_fixtures('gene_info.conf'))
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


@pytest.fixture()
def mock_preloader_gene_info_config(mocker, gscs):
    import preloaded.register
    original = preloaded.register.get

    def mock_get(key):
        print("mock func called!", key)
        if key == 'gene_sets_collections':
            return gscs
        return original(key)
    mocker.patch('preloaded.register.get', new=mock_get)


@pytest.fixture(scope='module')
def gene_info_cache_dir():
    cache_dir = path_to_fixtures('geneInfo', 'cache')
    shutil.rmtree(cache_dir, ignore_errors=True)
    assert not os.path.exists(cache_dir)
    os.makedirs(cache_dir)

    yield

    shutil.rmtree(cache_dir)
