import os

from dae.common_reports.config import CommonReportsParseConfig


def test_common_reports_config(
        common_reports_config, people_groups, filter_info):
    assert common_reports_config.id == 'Study1'
    assert common_reports_config.people_groups_info == people_groups
    assert common_reports_config.filter_info == filter_info
    assert common_reports_config.effect_groups == ['Missense']
    assert common_reports_config.effect_types == ['Frame-shift']
    assert common_reports_config.path == '/path/to/common_report'


def test_common_reports_parse_config(study1_config):
    common_reports_config = CommonReportsParseConfig.from_config(study1_config)

    assert common_reports_config.id == 'Study1'

    assert list(common_reports_config.people_groups_info.keys()) == \
        ['phenotype']

    people_groups_info = \
        common_reports_config.people_groups_info['phenotype']

    assert people_groups_info['name'] == 'Study phenotype'
    assert len(people_groups_info['domain']) == 4
    assert sorted(people_groups_info['domain'][0].keys()) == \
        sorted(['id', 'name', 'color'])
    assert sorted(people_groups_info['default'].keys()) == \
        sorted(['id', 'name', 'color'])
    assert people_groups_info['source'] == 'study.phenotype'

    filter_info = common_reports_config.filter_info

    assert list(filter_info['people_groups']) == ['phenotype']
    assert filter_info['groups']['Role'] == ['role']
    assert filter_info['groups']['Diagnosis'] == ['phenotype']
    assert filter_info['groups']['Role and Diagnosis'] == ['role', 'phenotype']
    assert filter_info['draw_all_families'] is False
    assert filter_info['families_count_show_id'] == 5
    assert filter_info['id'] == 'Study1'

    assert common_reports_config.effect_groups == []
    assert common_reports_config.effect_types == \
        ['Frame-shift', 'Missense']
    assert common_reports_config.path == \
        os.path.join(os.path.dirname(os.path.realpath(__file__)),
                     'fixtures/studies/Study1/common_report.json')


def test_common_reports_parse_config_missing_config(dataset2_config):
    common_reports_parse_config = \
        CommonReportsParseConfig.from_config(dataset2_config)

    assert common_reports_parse_config is None


def test_common_reports_parse_config_disabled(dataset3_config):
    common_reports_parse_config = \
        CommonReportsParseConfig.from_config(dataset3_config)

    assert common_reports_parse_config is None


def test_common_reports_parse_config_missing_groups(dataset4_config):
    common_reports_parse_config = \
        CommonReportsParseConfig.from_config(dataset4_config)

    assert common_reports_parse_config is None
