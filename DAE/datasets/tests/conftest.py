import pytest

from datasets.dataset import DatasetWrapper
from datasets.dataset_factory import DatasetFactory


@pytest.fixture(scope='session')
def dataset_factory():
    return DatasetFactory()


@pytest.fixture(scope='session')
def inheritance_trio_wrapper(dataset_factory):
    return dataset_factory.make_dataset(
        'inheritance_trio', 'fixtures/inheritance_trio', _class=DatasetWrapper)


@pytest.fixture(scope='session')
def quads2_wrapper(dataset_factory):
    return dataset_factory.make_dataset(
        'quads2', 'fixtures/quads2', _class=DatasetWrapper)
