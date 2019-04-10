from __future__ import unicode_literals

import pytest

import os
from copy import deepcopy
from collections import OrderedDict

from studies.study_definition import DirectoryEnabledStudiesDefinition
from studies.study_factory import StudyFactory
from studies.study_facade import StudyFacade
from studies.dataset_definition import DirectoryEnabledDatasetsDefinition
from studies.dataset_factory import DatasetFactory
from studies.dataset_facade import DatasetFacade
from studies.factory import VariantsDb
from configurable_entities.configuration import DAEConfig
from pheno.pheno_factory import PhenoFactory

from common_reports.filter import Filter, FilterObject, FilterObjects
from common_reports.people_group_info import PeopleGroupInfo, PeopleGroupsInfo
from common_reports.people_counter import PeopleCounter, PeopleCounters
from common_reports.family_counter import FamilyCounter, \
    FamiliesGroupCounter, FamiliesGroupCounters
from common_reports.family_report import FamiliesReport
from common_reports.denovo_report import EffectCell, EffectRow, \
    DenovoReportTable, DenovoReport
from common_reports.common_report import CommonReport
from common_reports.config import CommonReportsConfig, CommonReportsParseConfig
from common_reports.common_report_facade import CommonReportFacade


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
def study_definitions(dae_config_fixture):
    return DirectoryEnabledStudiesDefinition(
        studies_dir=studies_dir(),
        work_dir=fixtures_dir(),
        default_conf=dae_config_fixture.default_configuration_conf)


@pytest.fixture(scope='session')
def study_factory():
    return StudyFactory()


@pytest.fixture(scope='session')
def pheno_factory(dae_config_fixture):
    return PhenoFactory(dae_config_fixture)


@pytest.fixture(scope='session')
def study_facade(study_factory, study_definitions, pheno_factory):
    return StudyFacade(pheno_factory, study_factory=study_factory,
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
    return DatasetFacade(
        dataset_definitions=dataset_definitions,
        dataset_factory=dataset_factory,
        pheno_factory=pheno_factory)


@pytest.fixture(scope='session')
def vdb_fixture(dae_config_fixture):
    vdb = VariantsDb(dae_config_fixture)
    return vdb


@pytest.fixture(scope='session')
def common_report_facade(vdb_fixture):
    common_report_facade = CommonReportFacade(vdb_fixture)

    return common_report_facade


@pytest.fixture(scope='session')
def dae_config_fixture():
    dae_config = DAEConfig(fixtures_dir())
    return dae_config


@pytest.fixture(scope='session')
def study1(study_facade):
    return study_facade.get_study_wdae_wrapper("Study1")


@pytest.fixture(scope='session')
def study2(study_facade):
    return study_facade.get_study_wdae_wrapper("Study2")


@pytest.fixture(scope='session')
def study4(study_facade):
    return study_facade.get_study_wdae_wrapper("study4")


@pytest.fixture(scope='session')
def dataset1(dataset_facade):
    return dataset_facade.get_dataset_wdae_wrapper("Dataset1")


@pytest.fixture(scope='session')
def study1_config(study_facade):
    return study_facade.get_study_config("Study1")


@pytest.fixture(scope='session')
def dataset2_config(dataset_facade):
    return dataset_facade.get_dataset_config("Dataset2")


@pytest.fixture(scope='session')
def dataset3_config(dataset_facade):
    return dataset_facade.get_dataset_config("Dataset3")


@pytest.fixture(scope='session')
def dataset4_config(dataset_facade):
    return dataset_facade.get_dataset_config("Dataset4")


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
    people_group = {}
    if 'genotypeBrowser' in study1_config and study1_config.genotype_browser:
        genotype_browser = study1_config.genotype_browser
        people_group = genotype_browser.people_group

    people_groups = OrderedDict()
    for pg in people_group:
        people_groups[pg['id']] = pg

    return people_groups


@pytest.fixture(scope='session')
def people_group_info(people_groups, study2):
    return PeopleGroupInfo(
        people_groups['phenotype'], 'phenotype', study=study2
    )


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
def filter_object_from_list(filter_role, filter_people_group):
    return FilterObject.from_list([[filter_role, filter_people_group]])


@pytest.fixture(scope='function')
def filter_objects_simple(filter_object):
    return FilterObjects('Role', filter_objects=[filter_object])


@pytest.fixture(scope='session')
def filter_objects(study1, people_groups_info, groups):
    return FilterObjects.get_filter_objects(study1, people_groups_info, groups)


@pytest.fixture(scope='session')
def pc_s1_dad_and_phenotype1(study1, filter_objects):
    filter_object = None
    for fo in filter_objects[0].filter_objects:
        if fo.get_column_name() == 'dad and phenotype1':
            filter_object = fo
    assert filter_object

    return PeopleCounter(study1.families, filter_object)


@pytest.fixture(scope='session')
def pc_s1_mom_and_phenotype1(study1, filter_objects):
    filter_object = None
    for fo in filter_objects[0].filter_objects:
        if fo.get_column_name() == 'mom and phenotype1':
            filter_object = fo
    assert filter_object

    return PeopleCounter(study1.families, filter_object)


@pytest.fixture(scope='session')
def people_counters(study1, filter_objects):
    return PeopleCounters(study1.families, filter_objects[0])


@pytest.fixture(scope='session')
def families_groups_same(study1):
    return [study1.families['f1'], study1.families['f3'],
            study1.families['f6'], study1.families['f9'],
            study1.families['f10']]


@pytest.fixture(scope='session')
def families_groups(study1):
    return [study1.families['f4'], study1.families['f5'],
            study1.families['f7'], study1.families['f8']]


@pytest.fixture(scope='session')
def family_counter(study1, people_groups_info):
    return FamilyCounter(
        study1.families['f5'], 1,
        people_groups_info.get_people_group_info('phenotype')
    )


@pytest.fixture(scope='session')
def families_counter(families_groups, people_groups_info):
    return FamiliesGroupCounter(
        families_groups,
        people_groups_info.get_people_group_info('phenotype'),
        False, False
    )


@pytest.fixture(scope='session')
def families_counter_draw_all(families_groups, people_groups_info):
    return FamiliesGroupCounter(
        families_groups,
        people_groups_info.get_people_group_info('phenotype'),
        True, False
    )


@pytest.fixture(scope='session')
def families_counter_same(families_groups_same, people_groups_info):
    return FamiliesGroupCounter(
        families_groups_same,
        people_groups_info.get_people_group_info('phenotype'),
        False, False
    )


@pytest.fixture(scope='session')
def families_counters(study1, people_groups_info):
    return FamiliesGroupCounters(
        study1.families,
        people_groups_info.get_people_group_info('phenotype'),
        False, False
    )


@pytest.fixture(scope='session')
def families_report(study1, filter_objects, people_groups_info):
    return FamiliesReport(study1, people_groups_info, filter_objects)


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
def effect_with_filter_missense(dataset1, denovo_variants_ds1, filter_objects):
    filter_object = None
    for fo in filter_objects[0].filter_objects:
        if fo.get_column_name() == 'sib and phenotype2':
            filter_object = fo
    assert filter_object

    return EffectCell(
        dataset1, denovo_variants_ds1, filter_object, 'Missense'
    )


@pytest.fixture(scope='session')
def effect_with_filter_frame_shift(
        dataset1, denovo_variants_ds1, filter_objects):
    filter_object = None
    for fo in filter_objects[0].filter_objects:
        if fo.get_column_name() == 'prb and phenotype1':
            filter_object = fo
    assert filter_object

    return EffectCell(
        dataset1, denovo_variants_ds1, filter_object, 'Frame-shift'
    )


@pytest.fixture(scope='session')
def effect_with_filter_empty(dataset1, denovo_variants_ds1, filter_objects):
    filter_object = None
    for fo in filter_objects[0].filter_objects:
        if fo.get_column_name() == 'dad and unknown':
            filter_object = fo
    assert filter_object

    return EffectCell(
        dataset1, denovo_variants_ds1, filter_object, 'Frame-shift'
    )


@pytest.fixture(scope='session')
def effect(dataset1, denovo_variants_ds1, filter_objects):
    return EffectRow(
        dataset1, denovo_variants_ds1, 'Missense', filter_objects[0]
    )


@pytest.fixture(scope='session')
def denovo_report_table(dataset1, denovo_variants_ds1, filter_objects):
    return DenovoReportTable(
        dataset1, denovo_variants_ds1, ['Missense', 'Splice-site'],
        ['Frame-shift', 'Nonsense'], filter_objects[0]
    )


@pytest.fixture(scope='session')
def denovo_report(dataset1, filter_objects):
    return DenovoReport(
        dataset1, ['Missense'], ['Frame-shift'], filter_objects
    )


@pytest.fixture(scope='session')
def common_report(study4, common_reports_config):
    return CommonReport(study4, common_reports_config)


@pytest.fixture(scope='session')
def common_reports_config(study1, study1_config, people_groups, filter_info):
    common_report_config = \
        deepcopy(study1_config.study_config.get('commonReport', None))
    common_report_config['file'] = '/path/to/common_report'
    common_report_config['effect_groups'] = ['Missense']
    common_report_config['effect_types'] = ['Frame-shift']

    return CommonReportsConfig(
        study1.id, common_report_config, people_groups, filter_info
    )


@pytest.fixture(scope='session')
def common_reports_parse_config(study1_config):
    return CommonReportsParseConfig.from_config(study1_config)


@pytest.fixture(scope='session')
def common_reports_parse_config_missing_config(dataset2_config):
    return CommonReportsParseConfig.from_config(dataset2_config)


@pytest.fixture(scope='session')
def common_reports_parse_config_disabled(dataset3_config):
    return CommonReportsParseConfig.from_config(dataset3_config)


@pytest.fixture(scope='session')
def common_reports_parse_config_missing_groups(dataset4_config):
    return CommonReportsParseConfig.from_config(dataset4_config)


@pytest.fixture(scope='module')
def remove_common_reports(common_report_facade):
    all_configs = common_report_facade.get_all_common_report_configs()
    temp_files = [config.path for config in all_configs]

    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)

    yield

    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)
