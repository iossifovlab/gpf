import pytest

import os
from box import Box
from copy import deepcopy
from collections import OrderedDict

from dae.studies.factory import VariantsDb
from dae.configuration.dae_config_parser import DAEConfigParser

from dae.common_reports.filter import Filter, FilterObject, FilterObjects
from dae.common_reports.people_group_info import PeopleGroupsInfo
from dae.common_reports.common_report_facade import CommonReportFacade


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
def dae_config_fixture():
    dae_config = DAEConfigParser.read_and_parse_file_configuration(
        work_dir=fixtures_dir())
    return dae_config


@pytest.fixture(scope='session')
def vdb_fixture(dae_config_fixture):
    vdb = VariantsDb(dae_config_fixture)
    return vdb


@pytest.fixture(scope='session')
def common_report_facade(vdb_fixture):
    common_report_facade = CommonReportFacade(vdb_fixture)

    return common_report_facade


@pytest.fixture(scope='session')
def study1(vdb_fixture):
    return vdb_fixture.get_study_wdae_wrapper("Study1")


@pytest.fixture(scope='session')
def study2(vdb_fixture):
    return vdb_fixture.get_study_wdae_wrapper("Study2")


@pytest.fixture(scope='session')
def study4(vdb_fixture):
    return vdb_fixture.get_study_wdae_wrapper("study4")


@pytest.fixture(scope='session')
def dataset1(vdb_fixture):
    return vdb_fixture.get_dataset_wdae_wrapper("Dataset1")


@pytest.fixture(scope='session')
def study1_config(vdb_fixture):
    return vdb_fixture.get_study_config("Study1")


@pytest.fixture(scope='session')
def dataset2_config(vdb_fixture):
    return vdb_fixture.get_dataset_config("Dataset2")


@pytest.fixture(scope='session')
def dataset3_config(vdb_fixture):
    return vdb_fixture.get_dataset_config("Dataset3")


@pytest.fixture(scope='session')
def dataset4_config(vdb_fixture):
    return vdb_fixture.get_dataset_config("Dataset4")


@pytest.fixture(scope='session')
def groups():
    return {
        'Role and Diagnosis': ['role', 'phenotype']
    }


@pytest.fixture(scope='session')
def filter_info(groups):
    return {
        'people_groups': ['phenotype'],
        'groups': groups
    }


@pytest.fixture(scope='session')
def people_groups(study1_config):
    people_group = study1_config.people_group_config.people_group

    people_groups = OrderedDict()
    for pg in people_group:
        people_groups[pg['id']] = pg

    return people_groups


@pytest.fixture(scope='session')
def people_groups_info(study1, filter_info, people_groups):
    return PeopleGroupsInfo(study1, filter_info, people_groups)


@pytest.fixture(scope='session')
def filter_role():
    return Filter('role', 'mom', column_value='Mother')


@pytest.fixture(scope='session')
def filter_people_group():
    return Filter('phenotype', 'pheno', column_value='Pheno')


@pytest.fixture(scope='function')
def filter_object(filter_role):
    return FilterObject([filter_role])


@pytest.fixture(scope='session')
def filter_objects(study1, people_groups_info, groups):
    return FilterObjects.get_filter_objects(study1, people_groups_info, groups)


@pytest.fixture(scope='session')
def families_groups(study1):
    return [study1.families['f4'], study1.families['f5'],
            study1.families['f7'], study1.families['f8']]


@pytest.fixture(scope='session')
def denovo_variants_ds1(dataset1):
    denovo_variants = dataset1.query_variants(
        limit=None,
        inheritance='denovo',
    )
    denovo_variants = list(denovo_variants)

    assert len(denovo_variants) == 8

    return denovo_variants


@pytest.fixture(scope='session')
def common_reports_config(study1, study1_config, people_groups, filter_info):
    common_report_config = \
        deepcopy(study1_config.study_config.get('commonReport', None))
    common_report_config['id'] = 'Study1'
    common_report_config['file_path'] = '/path/to/common_report'
    common_report_config['effect_groups'] = ['Missense']
    common_report_config['effect_types'] = ['Frame-shift']
    common_report_config['people_groups_info'] = people_groups
    common_report_config['filter_info'] = filter_info

    return Box(common_report_config, camel_killer_box=True)


@pytest.fixture(scope='module')
def remove_common_reports(common_report_facade):
    all_configs = common_report_facade.get_all_common_report_configs()
    temp_files = [config.file_path for config in all_configs]

    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)

    yield

    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)
