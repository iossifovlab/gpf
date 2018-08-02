import pytest
import os

from datasets.dataset import DatasetWrapper
from datasets.dataset_factory import DatasetFactory
from datasets.datasets_definition import SingleFileDatasetsDefinition
from studies.study_definition import StudyDefinition


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


def load_dataset(fixtures_folder, dataset_factory, dataset_name):
    definition = SingleFileDatasetsDefinition(
        '{}.conf'.format(dataset_name), fixtures_folder)

    result = dataset_factory.get_dataset(
        definition.get_dataset_config(dataset_name))

    print(result)
    assert result is not None

    return result


@pytest.fixture(scope='session')
def study_definition():
    return StudyDefinition.from_config_file('studies.conf', fixtures_dir())


@pytest.fixture(scope='session')
def dataset_factory(study_definition):
    return DatasetFactory(
        _class=DatasetWrapper, studies_definition=study_definition)


@pytest.fixture(scope='session')
def fixtures_folder():
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'fixtures'
    )


@pytest.fixture(scope='session')
def inheritance_trio_wrapper(fixtures_folder, dataset_factory):
    return load_dataset(fixtures_folder, dataset_factory, 'inheritance_trio')


@pytest.fixture(scope='session')
def quads_f1_wrapper(fixtures_folder, dataset_factory):
    return load_dataset(fixtures_folder, dataset_factory, 'quads_f1')


@pytest.fixture(scope='session')
def quads_variant_types_wrapper(fixtures_folder, dataset_factory):
    return load_dataset(fixtures_folder, dataset_factory, 'quads_variant_types')


@pytest.fixture(scope='session')
def quads_two_families_wrapper(fixtures_folder, dataset_factory):
    return load_dataset(fixtures_folder, dataset_factory, 'quads_two_families')


@pytest.fixture(scope='session')
def quads_in_child(fixtures_folder, dataset_factory):
    return load_dataset(fixtures_folder, dataset_factory, 'quads_in_child')


@pytest.fixture(scope='session')
def quads_in_parent(fixtures_folder, dataset_factory):
    return load_dataset(fixtures_folder, dataset_factory, 'quads_in_parent')
