import pytest

from studies.study_definition import SingleFileStudiesDefinition
from study_groups.study_group import StudyGroupWrapper
from study_groups.study_group_definition import SingleFileStudiesGroupDefinition
from study_groups.study_group_factory import StudyGroupFactory
from study_groups.study_group_facade import StudyGroupFacade
from utils.fixtures import path_to_fixtures as _path_to_fixtures


def path_to_fixtures(path=None):
    return _path_to_fixtures('study_groups', path)


@pytest.fixture(scope='session')
def create_study_groups_definition():
    return lambda path: SingleFileStudiesGroupDefinition(path_to_fixtures(path))


@pytest.fixture(scope='session')
def basic_groups_definition(create_study_groups_definition):
    return create_study_groups_definition('basic.conf')


@pytest.fixture(scope='session')
def unknown_study_definition(create_study_groups_definition):
    return create_study_groups_definition('unknown_study.conf')


@pytest.fixture(scope='session')
def studies_definition():
    return SingleFileStudiesDefinition(work_dir=path_to_fixtures('studies'))


@pytest.fixture(scope='session')
def study_groups_factory(studies_definition):
    return StudyGroupFactory(studies_definition=studies_definition, _class=StudyGroupWrapper)


@pytest.fixture(scope='session')
def study_group_facade(basic_groups_definition, study_groups_factory):
    return StudyGroupFacade(
        study_group_definition=basic_groups_definition,
        study_group_factory=study_groups_factory
    )
