import pytest
import os

from studies.study_definition import SingleFileStudiesDefinition
from study_groups.study_group_definition import SingleFileStudiesGroupDefinition
from study_groups.study_group_factory import StudyGroupFactory


def in_fixtures_dir(path):
    args = [os.path.dirname(os.path.abspath(__file__)), 'fixtures']

    if path:
        args.append(path)

    return os.path.join(*args)


@pytest.fixture(scope='session')
def create_study_groups_definition():
    return lambda path: SingleFileStudiesGroupDefinition(in_fixtures_dir(path))


@pytest.fixture(scope='session')
def basic_groups_definition(create_study_groups_definition):
    return create_study_groups_definition('basic.conf')


@pytest.fixture(scope='session')
def unknown_study_definition(create_study_groups_definition):
    return create_study_groups_definition('unknown_study.conf')


@pytest.fixture(scope='session')
def studies_definition():
    return SingleFileStudiesDefinition(work_dir=in_fixtures_dir('studies'))


@pytest.fixture(scope='session')
def study_groups_factory(studies_definition):
    return StudyGroupFactory(studies_definition=studies_definition)
