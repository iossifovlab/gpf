import os
import pytest

from studies.study_config import StudyConfig
from studies.study_definition import StudyDefinition
from studies.study_factory import StudyFactory


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


@pytest.fixture()
def study_configs():
    return StudyConfig.list_from_config(work_dir=fixtures_dir())


@pytest.fixture()
def study_definition(study_configs):
    return StudyDefinition.from_config(study_configs)


@pytest.fixture()
def study_factory(study_definition):
    return StudyFactory(study_definition)
