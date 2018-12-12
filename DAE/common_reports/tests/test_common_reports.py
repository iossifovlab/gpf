from unittest.mock import patch, mock_open

import common_reports.common_report


def assert_common_reports(first, second):
    first['phenotype'] = sorted(first['phenotype'][1:-1].split(', '))
    second['phenotype'] = sorted(second['phenotype'][1:-1].split(', '))

    for el in range(len(first['families_report']['people_counters'])):
        first['families_report']['people_counters'][el]['phenotypes'].sort()
        second['families_report']['people_counters'][el]['phenotypes'].sort()
        first['families_report']['people_counters'][el]['counters'].sort(
            key=lambda counters: str(counters['phenotype']))
        second['families_report']['people_counters'][el]['counters'].sort(
            key=lambda counters: str(counters['phenotype']))
    for el in range(len(first['families_report']['families_counters'])):
        first['families_report']['families_counters'][el]['phenotypes'].sort()
        second['families_report']['families_counters'][el]['phenotypes'].sort()
        first['families_report']['families_counters'][el]['counters'].sort(
            key=lambda families_counters: str(families_counters['phenotype']))
        second['families_report']['families_counters'][el]['counters'].sort(
            key=lambda families_counters: str(families_counters['phenotype']))

    for rows_el in range(len(first['denovo_report']['tables'])):
        first['denovo_report']['tables'][rows_el]['phenotypes'].sort()
        second['denovo_report']['tables'][rows_el]['phenotypes'].sort()
        for row_el in\
                range(len(first['denovo_report']['tables'][rows_el]['rows'])):
            first['denovo_report']['tables'][rows_el]['rows'][row_el]['row']\
                .sort(key=lambda row: str(row['phenotype']))
            second['denovo_report']['tables'][rows_el]['rows'][row_el]['row']\
                .sort(key=lambda row: str(row['phenotype']))

    assert first == second


def test_common_reports_generator(common_reports_generator, output):
    with patch(common_reports.common_report.__name__ + '.open',
               new_callable=mock_open()):

        with patch('json.dump') as m_json:
            common_reports_generator.save_common_reports()
            assert m_json.assert_any_call
            for common_report_call in m_json.call_args_list:
                common_report = list(common_report_call)[0][0]
                common_report_output = output(common_report['study_name'])

                assert_common_reports(common_report, common_report_output)
