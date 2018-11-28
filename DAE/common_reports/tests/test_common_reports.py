from unittest.mock import mock_open, patch
from unittest import TestCase
from hamcrest import assert_that, has_entries


def assert_common_reports(first, second):
    first['phenotype'] = sorted(first['phenotype'].split(','))
    second['phenotype'] = sorted(second['phenotype'].split(','))

    first['families_report']['phenotypes'].sort()
    second['families_report']['phenotypes'].sort()
    for el in range(len(first['families_report']['people_counters'])):
        first['families_report']['people_counters'][el]['counters'].sort(
            key=lambda counters: str(counters['phenotype']))
        second['families_report']['people_counters'][el]['counters'].sort(
            key=lambda counters: str(counters['phenotype']))
    first['families_report']['families_counters'].sort(
        key=lambda families_counters: str(families_counters['phenotype']))
    second['families_report']['families_counters'].sort(
        key=lambda families_counters: str(families_counters['phenotype']))

    first['denovo_report']['phenotypes'].sort()
    second['denovo_report']['phenotypes'].sort()
    for rows_el in range(len(first['denovo_report']['tables'])):
        for row_el in\
                range(len(first['denovo_report']['tables'][rows_el]['rows'])):
            first['denovo_report']['tables'][rows_el]['rows'][row_el]['row']\
                .sort(key=lambda row: str(row['phenotype']))
            second['denovo_report']['tables'][rows_el]['rows'][row_el]['row']\
                .sort(key=lambda row: str(row['phenotype']))

    assert first == second


def test_common_reports_generator(common_reports_generator, output):
    with patch('json.dump') as m_json:
        common_reports_generator.save_common_reports()

        for common_report_call in m_json.call_args_list:
            common_report = list(common_report_call)[0][0]
            common_report_output = output(common_report['study_name'])

            assert_common_reports(common_report, common_report_output)
