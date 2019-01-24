import json

import common_reports.common_report


def assert_common_reports(first, second):
    first['phenotype'].sort()
    second['phenotype'].sort()

    for el in range(len(first['families_report']['people_counters'])):
        first['families_report']['people_counters'][el]['columns'].sort()
        second['families_report']['people_counters'][el]['columns'].sort()
        first['families_report']['people_counters'][el]['counters'].sort(
            key=lambda counters: str(counters['column']))
        second['families_report']['people_counters'][el]['counters'].sort(
            key=lambda counters: str(counters['column']))
    for el in range(len(first['families_report']['families_counters'])):
        first['families_report']['families_counters'][el]['phenotypes'].sort()
        second['families_report']['families_counters'][el]['phenotypes'].sort()
        first['families_report']['families_counters'][el]['counters'].sort(
            key=lambda families_counters: len(families_counters))
        second['families_report']['families_counters'][el]['counters'].sort(
            key=lambda families_counters: len(families_counters))

    for rows_el in range(len(first['denovo_report']['tables'])):
        first['denovo_report']['tables'][rows_el]['columns'].sort()
        second['denovo_report']['tables'][rows_el]['columns'].sort()
        for row_el in\
                range(len(first['denovo_report']['tables'][rows_el]['rows'])):
            first['denovo_report']['tables'][rows_el]['rows'][row_el]['row']\
                .sort(key=lambda row: str(row['column']))
            second['denovo_report']['tables'][rows_el]['rows'][row_el]['row']\
                .sort(key=lambda row: str(row['column']))

    assert first == second


def test_common_reports_generator(mocker, common_reports_generator, output):
    with mocker.patch(common_reports.common_report.__name__ + '.open',
                      new_callable=mocker.mock_open()):

        mocker.patch('json.dump')

        common_reports_generator.save_common_reports()

        assert json.dump.call_count == 4

        for common_report_call in json.dump.call_args_list:
            common_report = list(common_report_call)[0][0]
            common_report_output = output(common_report['study_name'])

            assert_common_reports(common_report, common_report_output)
