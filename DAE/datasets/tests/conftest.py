import pytest

from datasets.dataset_factory import DatasetFactory


@pytest.fixture(scope='session')
def dataset_factory():
    return DatasetFactory()


@pytest.fixture(scope='session')
def inheritance_trio(dataset_factory):
    return dataset_factory.make_dataset(
        'inheritance_trio', 'fixtures/inheritance_trio')
