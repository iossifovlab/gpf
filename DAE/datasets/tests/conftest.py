import pytest
import os

from datasets.dataset import DatasetWrapper
from datasets.dataset_factory import DatasetFactory
from datasets.datasets_definition import SingleFileDatasetsDefinition


def create_dataset_wrapper_factory(dataset_definition):
    return DatasetFactory(dataset_definition, _class=DatasetWrapper)


@pytest.fixture(scope='session')
def fixtures_folder():
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'fixtures'
    )


@pytest.fixture(scope='session')
def inheritance_trio_wrapper(fixtures_folder):
    definition = SingleFileDatasetsDefinition(
        'inheritance_trio.conf', fixtures_folder)

    dataset_factory = create_dataset_wrapper_factory(definition)

    return dataset_factory.get_dataset('inheritance_trio')


@pytest.fixture(scope='session')
def quads2_wrapper(fixtures_folder):
    definition = SingleFileDatasetsDefinition(
        'quads2.conf', fixtures_folder)

    dataset_factory = create_dataset_wrapper_factory(definition)
    print(dataset_factory.get_dataset('quads2'))

    return dataset_factory.get_dataset('quads2')
