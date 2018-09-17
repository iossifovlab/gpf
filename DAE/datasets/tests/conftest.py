import pytest
import os
import functools

from datasets.dataset import DatasetWrapper
from datasets.dataset_facade import DatasetFacade
from datasets.dataset_factory import DatasetFactory
from datasets.datasets_definition import SingleFileDatasetsDefinition
from studies.study_definition import SingleFileStudiesDefinition
from study_groups.study_group_definition import SingleFileStudiesGroupDefinition


def fixtures_dir(path):
    args = [os.path.dirname(os.path.abspath(__file__)), 'fixtures']

    if path:
        args.append(path)

    return os.path.join(*args)


def load_dataset(fixtures_folder, dataset_factory, dataset_name):
    definition = SingleFileDatasetsDefinition(
        '{}.conf'.format(dataset_name), fixtures_folder)

    result = dataset_factory.get_dataset(
        definition.get_dataset_config(dataset_name))

    assert result is not None

    return result


@pytest.fixture(scope='session')
def dataset_facade(dataset_factory):
    return lambda dataset_id: \
        DatasetFacade(
            dataset_definition=SingleFileDatasetsDefinition(
                dataset_id, fixtures_dir(None)),
            dataset_factory=dataset_factory
        )


@pytest.fixture(scope='session')
def study_definition():
    return SingleFileStudiesDefinition(
        'studies.conf', fixtures_dir('studies'))


@pytest.fixture(scope='session')
def basic_study_group_definition(study_definition):
    return SingleFileStudiesGroupDefinition(
        'study_groups.conf', fixtures_dir('studies')
    )


@pytest.fixture(scope='session')
def dataset_factory(basic_study_group_definition, study_definition):
    return DatasetFactory(
        _class=DatasetWrapper,
        study_definition=study_definition,
        study_group_definition=basic_study_group_definition)


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
