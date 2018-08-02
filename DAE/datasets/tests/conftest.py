import pytest
import os

from datasets.dataset import DatasetWrapper
from datasets.dataset_factory import DatasetFactory
from datasets.datasets_definition import SingleFileDatasetsDefinition


def create_dataset_wrapper_factory():
    return DatasetFactory(_class=DatasetWrapper)


def load_dataset(fixtures_folder, dataset_name):
    definition = SingleFileDatasetsDefinition(
        '{}.conf'.format(dataset_name), fixtures_folder)

    dataset_factory = create_dataset_wrapper_factory()
    result = dataset_factory.get_dataset(
        definition.get_dataset_config(dataset_name))

    print(result)
    assert result is not None

    return result


@pytest.fixture(scope='session')
def fixtures_folder():
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'fixtures'
    )


@pytest.fixture(scope='session')
def inheritance_trio_wrapper(fixtures_folder):
    return load_dataset(fixtures_folder, 'inheritance_trio')


@pytest.fixture(scope='session')
def quads_f1_wrapper(fixtures_folder):
    return load_dataset(fixtures_folder, 'quads_f1')


@pytest.fixture(scope='session')
def quads_variant_types_wrapper(fixtures_folder):
    return load_dataset(fixtures_folder, 'quads_variant_types')


@pytest.fixture(scope='session')
def quads_two_families_wrapper(fixtures_folder):
    return load_dataset(fixtures_folder, 'quads_two_families')


@pytest.fixture(scope='session')
def quads_in_child(fixtures_folder):
    return load_dataset(fixtures_folder, 'quads_in_child')


@pytest.fixture(scope='session')
def quads_in_parent(fixtures_folder):
    return load_dataset(fixtures_folder, 'quads_in_parent')
