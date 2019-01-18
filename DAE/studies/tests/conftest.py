import os
import pytest

from studies.study_definition import DirectoryEnabledStudiesDefinition
from studies.study_factory import StudyFactory


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


def studies_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures/studies'))


@pytest.fixture(scope='session')
def study_configs(study_definition):
    return list(study_definition.configs.values())


@pytest.fixture(scope='session')
def study_definition():
    return DirectoryEnabledStudiesDefinition(
        studies_dir=studies_dir(),
        work_dir=fixtures_dir())


@pytest.fixture(scope='session')
def study_factory():
    return StudyFactory()


@pytest.fixture(scope='session')
def test_study(study_factory, study_definition):
    return study_factory.make_study(
        study_definition.get_study_config('quads_f1'))
