import pytest
import os

from datasets.dataset_facade import DatasetFacade
from datasets.dataset_factory import DatasetFactory
from datasets.datasets_definition import SingleFileDatasetsDefinition
from studies.study_definition import SingleFileStudiesDefinition
from study_groups.study_group import StudyGroupWrapper
from study_groups.study_group_definition import SingleFileStudiesGroupDefinition
from study_groups.study_group_factory import StudyGroupFactory

from utils.fixtures import change_environment


def fixtures_dir(path=None):
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


@pytest.fixture(scope='module')
def dataset_facade(dataset_factory):
    return lambda dataset_definition: \
        DatasetFacade(
            dataset_definition=dataset_definition,
            dataset_factory=dataset_factory
        )


@pytest.fixture(scope='module')
def study_groups_factory(study_definition):
    return StudyGroupFactory(
        studies_definition=study_definition, _class=StudyGroupWrapper)


@pytest.fixture(scope='module')
def study_definition():
    return SingleFileStudiesDefinition(
        'studies.conf', fixtures_dir('studies'))


@pytest.fixture(scope='module')
def basic_study_groups_definition(study_definition):
    return SingleFileStudiesGroupDefinition(
        'study_groups.conf', fixtures_dir('studies')
    )


@pytest.fixture(scope='module')
def dataset_factory(basic_study_groups_definition, study_groups_factory):
    return DatasetFactory(
        study_group_factory=study_groups_factory,
        study_group_definition=basic_study_groups_definition)


@pytest.fixture(scope='module')
def datasets_folder():
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'fixtures/datasets'
    )


@pytest.fixture(scope='module')
def inheritance_trio_wrapper(datasets_folder, dataset_factory):
    return load_dataset(datasets_folder, dataset_factory, 'inheritance_trio')


@pytest.fixture(scope='module')
def quads_f1_wrapper(datasets_folder, dataset_factory):
    return load_dataset(datasets_folder, dataset_factory, 'quads_f1')


@pytest.fixture(scope='module')
def quads_variant_types_wrapper(datasets_folder, dataset_factory):
    return load_dataset(datasets_folder, dataset_factory, 'quads_variant_types')


@pytest.fixture(scope='module')
def quads_two_families_wrapper(datasets_folder, dataset_factory):
    return load_dataset(datasets_folder, dataset_factory, 'quads_two_families')


@pytest.fixture(scope='module')
def quads_in_child(datasets_folder, dataset_factory):
    return load_dataset(datasets_folder, dataset_factory, 'quads_in_child')


@pytest.fixture(scope='module')
def quads_in_parent(datasets_folder, dataset_factory):
    return load_dataset(datasets_folder, dataset_factory, 'quads_in_parent')


@pytest.fixture(scope='module')
def pheno_conf_path():
    new_envs = {
        'DAE_DB_DIR': fixtures_dir()
    }

    for val in change_environment(new_envs):
        yield val
