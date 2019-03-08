import pytest
import os
import shutil

from DAE import Config
from datasets_api.studies_manager import get_studies_manager
from studies.study_definition import SingleFileStudiesDefinition
from study_groups.study_group_definition import SingleFileStudiesGroupDefinition

from utils.fixtures import path_to_fixtures as _path_to_fixtures


def path_to_fixtures(*args, package='wdae'):
    return _path_to_fixtures('gene_sets', *args, package=package)


def mock_property(mocker):
    def result(property, mock_value):
        file_mock = mocker.patch(property, new_callable=mocker.PropertyMock)
        file_mock.return_value = mock_value
    return result


def mock_preload(mocker, mocked_key, func, original):
    def mock_get(key):
        if key == mocked_key: # gene_sets_collections':
            return func()
        return original(key)
    mocker.patch('preloaded.register.get', new=mock_get)


@pytest.fixture(scope='session')
def studies_definition():
    return SingleFileStudiesDefinition(
        path_to_fixtures('studies', 'studies.conf'),
        path_to_fixtures('studies'))


@pytest.fixture(scope='session')
def basic_study_groups_definition():
    return SingleFileStudiesGroupDefinition(
        path_to_fixtures('studies', 'study_groups.conf'))


@pytest.fixture()
def mocked_dataset_config(mocker):
    mp = mock_property(mocker)

    mp('Config.Config.geneInfoDBconfFile', path_to_fixtures('gene_info.conf'))
    mp('Config.Config.geneInfoDBdir', path_to_fixtures())
    mp('Config.Config.daeDir', path_to_fixtures())

    return Config()


@pytest.fixture()
def mock_preloader_gene_info_config(mocker, gscs):
    import preloaded.register
    original = preloaded.register.get

    def mock_func():
        return gscs

    mock_preload(mocker, 'gene_sets_collections', mock_func, original)


@pytest.fixture()
def datasets_from_fixtures(db, settings):
    old_dataset_path = os.environ['DAE_DATA_DIR']

    os.environ['DAE_DATA_DIR'] = path_to_fixtures()
    print("REPLACING DAE_DATA_DIR")
    get_studies_manager().reload_dataset_facade()

    yield

    os.environ['DAE_DATA_DIR'] = old_dataset_path


@pytest.fixture(scope='session')
def gene_info_cache_dir():
    fixtures_dir = path_to_fixtures()
    module_dir = os.path.dirname(fixtures_dir)
    if not os.path.exists(module_dir):
        raise EnvironmentError(
            'Module "{}" does not exist..'.format(module_dir))
    cache_dir = path_to_fixtures('geneInfo', 'cache')
    shutil.rmtree(cache_dir, ignore_errors=True)
    assert not os.path.exists(cache_dir)
    os.makedirs(cache_dir)

    yield

    shutil.rmtree(cache_dir)
