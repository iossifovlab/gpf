import os
import pytest

from studies.study_config import StudyConfig
from studies.study_definition import StudyDefinition
from studies.study_factory import StudyFactory


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


def fixtures_config():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures/studies.conf'))


@pytest.fixture(scope='session')
def study_configs():
    return StudyDefinition.list_from_config(
        fixtures_config(), fixtures_dir(), StudyConfig)


@pytest.fixture(scope='session')
def study_definition(study_configs):
    return StudyDefinition.from_single_file(work_dir=fixtures_dir())


@pytest.fixture(scope='session')
def study_factory():
    return StudyFactory()


@pytest.fixture(scope='session')
def test_study(study_factory, study_definition):
    return study_factory.make_study(study_definition.get_study_config('test'))
