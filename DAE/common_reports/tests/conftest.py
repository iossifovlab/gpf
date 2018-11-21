import pytest

import os
from box import Box

from common_reports.common_report import CommonReportsGenerator
from study_groups.study_group_facade import StudyGroupFacade
from studies.study_facade import StudyFacade
from studies.study_definition import SingleFileStudiesDefinition
from study_groups.study_group_definition import\
    SingleFileStudiesGroupDefinition
from study_groups.study_group_factory import StudyGroupFactory
from utils.fixtures import path_to_fixtures as _path_to_fixtures


def path_to_fixtures(path=None):
    return _path_to_fixtures('common_reports', path)


@pytest.fixture(scope='session')
def common_reports_config():
    return Box({
        "commonReportsConfFile":
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         'fixtures/commonReports.conf')
    })


@pytest.fixture(scope='session')
def studies_definition():
    return SingleFileStudiesDefinition(work_dir=path_to_fixtures('studies'))


@pytest.fixture(scope='session')
def study_facade(studies_definition):
    return StudyFacade(
        study_definition=studies_definition
    )


@pytest.fixture(scope='session')
def study_groups_definition():
    return SingleFileStudiesGroupDefinition(
        path_to_fixtures('study_groups.conf'))


@pytest.fixture(scope='session')
def study_groups_factory(studies_definition):
    return StudyGroupFactory(studies_definition=studies_definition)


@pytest.fixture(scope='session')
def study_group_facade(study_groups_definition, study_groups_factory):
    return StudyGroupFacade(
        study_group_definition=study_groups_definition,
        study_group_factory=study_groups_factory
    )


@pytest.fixture(scope='session')
def common_reports_generator(
        common_reports_config, study_facade, study_group_facade):
    common_reports_generator = CommonReportsGenerator(
        study_facade=study_facade, study_group_facade=study_group_facade,
        config=common_reports_config)

    return common_reports_generator
