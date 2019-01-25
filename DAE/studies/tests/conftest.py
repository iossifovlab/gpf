from __future__ import unicode_literals

import os
import pytest

from studies.study_definition import DirectoryEnabledStudiesDefinition
from studies.study_factory import StudyFactory
from studies.study_facade import StudyFacade
from studies.study_wrapper import StudyWrapper
from studies.dataset_definition import DirectoryEnabledDatasetsDefinition
from studies.dataset_factory import DatasetFactory


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


def studies_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures/studies'))


def datasets_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures/datasets'))


@pytest.fixture(scope='session')
def study_configs(study_definition):
    return list(study_definition.configs.values())


@pytest.fixture(scope='session')
def study_definitions():
    return DirectoryEnabledStudiesDefinition(
        studies_dir=studies_dir(),
        work_dir=fixtures_dir())


@pytest.fixture(scope='session')
def study_factory():
    return StudyFactory()


@pytest.fixture(scope='session')
def study_facade(study_factory, study_definitions):
    return StudyFacade(
        study_factory=study_factory, study_definition=study_definitions)


@pytest.fixture(scope='session')
def quads_f1_config(study_definitions):
    return study_definitions.get_study_config('quads_f1')


def load_study(study_factory, study_definitions, study_name):
    config = study_definitions.get_study_config(study_name)

    result = study_factory.make_study(config)
    assert result is not None
    return result


@pytest.fixture(scope='session')
def inheritance_trio(study_factory, study_definitions):
    return load_study(study_factory, study_definitions, 'inheritance_trio')


@pytest.fixture(scope='session')
def quads_f1(study_factory, study_definitions):
    return load_study(study_factory, study_definitions, 'quads_f1')


@pytest.fixture(scope='session')
def quads_variant_types(study_factory, study_definitions):
    return load_study(study_factory, study_definitions, 'quads_variant_types')


@pytest.fixture(scope='session')
def quads_two_families(study_factory, study_definitions):
    return load_study(study_factory, study_definitions, 'quads_two_families')


@pytest.fixture(scope='session')
def quads_in_child(study_factory, study_definitions):
    return load_study(study_factory, study_definitions, 'quads_in_child')


@pytest.fixture(scope='session')
def quads_in_parent(study_factory, study_definitions):
    return load_study(study_factory, study_definitions, 'quads_in_parent')


@pytest.fixture(scope='session')
def inheritance_trio_wrapper(inheritance_trio):
    return StudyWrapper(inheritance_trio)


@pytest.fixture(scope='session')
def quads_f1_wrapper(quads_f1):
    return StudyWrapper(quads_f1)


@pytest.fixture(scope='session')
def quads_variant_types_wrapper(quads_variant_types):
    return StudyWrapper(quads_variant_types)


@pytest.fixture(scope='session')
def quads_two_families_wrapper(quads_two_families):
    return StudyWrapper(quads_two_families)


@pytest.fixture(scope='session')
def quads_in_child_wrapper(quads_in_child):
    return StudyWrapper(quads_in_child)


@pytest.fixture(scope='session')
def quads_in_parent_wrapper(quads_in_parent):
    return StudyWrapper(quads_in_parent)


@pytest.fixture(scope='session')
def dataset_definitions(study_facade):
    return DirectoryEnabledDatasetsDefinition(
        study_facade,
        datasets_dir=datasets_dir(),
        work_dir=fixtures_dir())


@pytest.fixture(scope='session')
def quads_composite_dataset_config(dataset_definitions):
    return dataset_definitions.get_dataset_config('quads_composite')


@pytest.fixture(scope='session')
def composite_dataset_config(dataset_definitions):
    return dataset_definitions.get_dataset_config('composite_dataset')


@pytest.fixture(scope='session')
def dataset_factory(study_facade):
    return DatasetFactory(study_facade=study_facade)


def load_dataset(dataset_factory, dataset_definitions, dataset_name):
    config = dataset_definitions.get_dataset_config(dataset_name)

    result = dataset_factory.make_dataset(config)
    assert result is not None
    return result


@pytest.fixture(scope='session')
def inheritance_trio_dataset(dataset_factory, dataset_definitions):
    return load_dataset(
        dataset_factory, dataset_definitions, 'inheritance_trio')


@pytest.fixture(scope='session')
def inheritance_trio_dataset_wrapper(inheritance_trio_dataset):
    return StudyWrapper(inheritance_trio_dataset)


@pytest.fixture(scope='session')
def quads_two_families_dataset(dataset_factory, dataset_definitions):
    return load_dataset(
        dataset_factory, dataset_definitions, 'quads_two_families')


@pytest.fixture(scope='session')
def quads_two_families_dataset_wrapper(quads_two_families_dataset):
    return StudyWrapper(quads_two_families_dataset)


@pytest.fixture(scope='session')
def quads_f1_dataset(dataset_factory, dataset_definitions):
    return load_dataset(
        dataset_factory, dataset_definitions, 'quads_f1')


@pytest.fixture(scope='session')
def quads_f1_dataset_wrapper(quads_f1_dataset):
    return StudyWrapper(quads_f1_dataset)


@pytest.fixture(scope='session')
def quads_variant_types_dataset(dataset_factory, dataset_definitions):
    return load_dataset(
        dataset_factory, dataset_definitions, 'quads_variant_types')


@pytest.fixture(scope='session')
def quads_variant_types_dataset_wrapper(quads_variant_types_dataset):
    return StudyWrapper(quads_variant_types_dataset)


@pytest.fixture(scope='session')
def quads_in_child_dataset(dataset_factory, dataset_definitions):
    return load_dataset(
        dataset_factory, dataset_definitions, 'quads_in_child')


@pytest.fixture(scope='session')
def quads_in_child_dataset_wrapper(quads_in_child_dataset):
    return StudyWrapper(quads_in_child_dataset)


@pytest.fixture(scope='session')
def quads_in_parent_dataset(dataset_factory, dataset_definitions):
    return load_dataset(
        dataset_factory, dataset_definitions, 'quads_in_parent')


@pytest.fixture(scope='session')
def quads_in_parent_dataset_wrapper(quads_in_parent_dataset):
    return StudyWrapper(quads_in_parent_dataset)
