from __future__ import unicode_literals

import os
import pytest
from box import Box

from pheno.pheno_factory import PhenoFactory
from studies.study_definition import DirectoryEnabledStudiesDefinition
from studies.study_factory import StudyFactory
from studies.study_facade import StudyFacade
from studies.dataset_definition import DirectoryEnabledDatasetsDefinition
from studies.dataset_factory import DatasetFactory
from studies.dataset_facade import DatasetFacade
from configurable_entities.configuration import DAEConfig
from datasets_api.views import DatasetView
from datasets_api.models import Dataset


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
def study_factory():
    return StudyFactory()


@pytest.fixture(scope='session')
def study_definitions(dae_config_fixture):
    return DirectoryEnabledStudiesDefinition(
        studies_dir=studies_dir(),
        work_dir=fixtures_dir(),
        default_conf=dae_config_fixture.default_configuration_conf)


@pytest.fixture(scope='session')
def study_facade(study_factory, study_definitions, pheno_factory):
    return StudyFacade(
        pheno_factory, study_factory=study_factory,
        study_definition=study_definitions)


@pytest.fixture(scope='session')
def dataset_definitions(study_facade, dae_config_fixture):
    return DirectoryEnabledDatasetsDefinition(
        study_facade,
        datasets_dir=datasets_dir(),
        work_dir=fixtures_dir(),
        default_conf=dae_config_fixture.default_configuration_conf)


@pytest.fixture(scope='session')
def dataset_factory(study_facade):
    return DatasetFactory(study_facade=study_facade)


@pytest.fixture(scope='session')
def dataset_facade(dataset_definitions, dataset_factory, pheno_factory):
    return DatasetFacade(dataset_definitions, dataset_factory, pheno_factory)


@pytest.fixture(scope='session')
def dataset_view(dataset_facade):
    return DatasetView(dataset_facade)


@pytest.fixture(scope='session')
def pheno_factory():
    return PhenoFactory()


@pytest.fixture(scope='session')
def user():
    return Box({'user': {'has_perm': lambda view, dataset: True}})


@pytest.fixture
def recreate_dataset_perm():
    Dataset.recreate_dataset_perm('composite_dataset', [])
    Dataset.recreate_dataset_perm('inheritance_trio', [])
    Dataset.recreate_dataset_perm('quads_composite', [])
    Dataset.recreate_dataset_perm('quads_f1', [])
    Dataset.recreate_dataset_perm('quads_in_child', [])
    Dataset.recreate_dataset_perm('quads_in_parent', [])
    Dataset.recreate_dataset_perm('quads_two_families', [])
    Dataset.recreate_dataset_perm('quads_variant_types', [])


@pytest.fixture(scope='session')
def dae_config_fixture():
    dae_config = DAEConfig(fixtures_dir())
    return dae_config
