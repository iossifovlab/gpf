import os


def test_common_reports_config(
        common_reports_config, people_groups, filter_info):
    assert common_reports_config.id == 'Study1'
    assert common_reports_config.people_groups_info == people_groups
    assert common_reports_config.filter_info == filter_info
    assert common_reports_config.effect_groups == []
    assert common_reports_config.effect_types == 'Frame-shift,Missense'
    assert common_reports_config.path == '/path/to/common_report'


def test_common_reports_parse_config(common_reports_parse_config):
    assert common_reports_parse_config.id == 'Study1'

    assert list(common_reports_parse_config.people_groups_info.keys()) == \
        ['phenotype']

    people_groups_info = \
        common_reports_parse_config.people_groups_info['phenotype']

    assert people_groups_info['name'] == 'Study phenotype'
    assert len(people_groups_info['domain']) == 4
    assert sorted(people_groups_info['domain'][0].keys()) == \
        sorted(['id', 'name', 'color'])
    assert sorted(people_groups_info['unaffected'].keys()) == \
        sorted(['id', 'name', 'color'])
    assert sorted(people_groups_info['default'].keys()) == \
        sorted(['id', 'name', 'color'])
    assert people_groups_info['source'] == 'study.phenotype'

    filter_info = common_reports_parse_config.filter_info

    assert list(filter_info['people_groups']) == ['phenotype']
    assert filter_info['groups']['Role'] == ['role']
    assert filter_info['groups']['Diagnosis'] == ['phenotype']
    assert filter_info['groups']['Role and Diagnosis'] == ['role', 'phenotype']
    assert filter_info['draw_all_families'] is False
    assert filter_info['families_count_show_id'] == 5
    assert filter_info['id'] == 'Study1'

    assert common_reports_parse_config.effect_groups == []
    assert common_reports_parse_config.effect_types == \
        ['Frame-shift', 'Missense']
    assert common_reports_parse_config.path == \
        os.path.join(os.path.dirname(os.path.realpath(__file__)),
                     'fixtures/studies/Study1/common_report.json')


def test_common_reports_parse_config_missing_config(
        common_reports_parse_config_missing_config):
    assert common_reports_parse_config_missing_config is None


def test_common_reports_parse_config_disabled(
        common_reports_parse_config_disabled):
    assert common_reports_parse_config_disabled is None


def test_common_reports_parse_config_missing_groups(
        common_reports_parse_config_missing_groups):
    assert common_reports_parse_config_missing_groups is None
