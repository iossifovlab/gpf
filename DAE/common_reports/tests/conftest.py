from __future__ import unicode_literals

import pytest
import os

import json
from collections import OrderedDict

from common_reports.common_report import CommonReportsGenerator
from common_reports.config import CommonReportsConfigs

from studies.study_definition import DirectoryEnabledStudiesDefinition
from studies.study_factory import StudyFactory
from studies.study_facade import StudyFacade
from studies.dataset_definition import DirectoryEnabledDatasetsDefinition
from studies.dataset_factory import DatasetFactory
from studies.dataset_facade import DatasetFacade


def fixtures_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures'))


def studies_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures/studies'))


def datasets_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures/datasets'))


def expected_output_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'fixtures/expected_output'))


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
def dataset_definitions(study_facade):
    return DirectoryEnabledDatasetsDefinition(
        study_facade,
        datasets_dir=datasets_dir(),
        work_dir=fixtures_dir())


@pytest.fixture(scope='session')
def dataset_factory(study_facade):
    return DatasetFactory(study_facade=study_facade)


@pytest.fixture(scope='session')
def dataset_facade(dataset_definitions, dataset_factory):
    return DatasetFacade(
        dataset_definitions=dataset_definitions,
        dataset_factory=dataset_factory)


def load_dataset(dataset_factory, dataset_definitions, dataset_name):
    config = dataset_definitions.get_dataset_config(dataset_name)

    result = dataset_factory.make_dataset(config)
    assert result is not None
    return result


@pytest.fixture(scope='session')
def common_reports_config(study_facade, dataset_facade):
    common_reports_config = CommonReportsConfigs()
    common_reports_config.scan_directory(studies_dir(), study_facade)
    common_reports_config.scan_directory(datasets_dir(), dataset_facade)

    return common_reports_config


@pytest.fixture(scope='session')
def common_reports_generator(common_reports_config):
    common_reports_generator = CommonReportsGenerator(common_reports_config)

    return common_reports_generator


@pytest.fixture(scope='session')
def output():
    def get_output(name):
        output_filename = os.path.join(
            expected_output_dir(),
            name + '.json'
        )
        with open(output_filename) as o:
            output = json.load(o, object_pairs_hook=OrderedDict)

        return output

    return get_output
