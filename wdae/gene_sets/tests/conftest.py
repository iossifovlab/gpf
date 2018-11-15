import pytest
import os
import shutil

from DAE import Config
from DAE import GeneInfoConfig
from DAE import GeneSetsCollections
from studies.study_definition import SingleFileStudiesDefinition
from study_groups.study_group_definition import SingleFileStudiesGroupDefinition
from datasets.datasets_definition import SingleFileDatasetsDefinition
from datasets_api.models import Dataset
# Used by pytest
from study_groups.tests.conftest import study_group_facade, study_groups_factory
from datasets.tests.conftest import dataset_facade, dataset_factory
from users_api.tests.conftest import logged_in_user, active_user

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


@pytest.fixture(scope='session')
def dataset_definition():
    return SingleFileDatasetsDefinition('datasets.conf', path_to_fixtures())


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
    return GeneSetsCollections(
        study_group_facade=study_group_facade, config=gene_info_config)


@pytest.fixture()
def mock_preloader_gene_info_config(mocker, gscs):
    import preloaded.register
    original = preloaded.register.get

    def mock_func():
        return gscs

    mock_preload(mocker, 'gene_sets_collections', mock_func, original)


@pytest.fixture(scope='module')
def datasets_from_fixtures():
    old_dataset_path = os.environ['DAE_DATA_DIR']

    os.environ['DAE_DATA_DIR'] = path_to_fixtures()

    print("REPLACING DAE_DATA_DIR")

    yield

    os.environ['DAE_DATA_DIR'] = old_dataset_path
    # import preloaded.register
    # original = preloaded.register.get
    # ds_factory = dataset_facade(dataset_definition)
    #
    # print("inside mocker: ", ds_factory.get_all_dataset_ids())
    #
    # mocker.patch(
    #     'datasets_api.datasets_preload.DatasetsPreload.get_facade',
    #     return_value=ds_factory)


@pytest.fixture()
def dataset_facade_object(dataset_definition, dataset_facade):
    print("creating dataset facade object")
    return dataset_facade(dataset_definition)


@pytest.fixture()
def dataset_permissions(db, dataset_facade_object):
    for dataset in dataset_facade_object.get_all_datasets():
        Dataset.recreate_dataset_perm(dataset.id, [])


@pytest.fixture(scope='session')
def gene_info_cache_dir():
    cache_dir = path_to_fixtures('geneInfo', 'cache')
    shutil.rmtree(cache_dir, ignore_errors=True)
    assert not os.path.exists(cache_dir)
    os.makedirs(cache_dir)

    yield

    shutil.rmtree(cache_dir)
