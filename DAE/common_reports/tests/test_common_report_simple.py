from pprint import pprint

from common_reports.common_report import CommonReport


def test_common_report_simple(common_reports_query_objects):
    assert common_reports_query_objects is not None

    print([
        st.name
        for st in common_reports_query_objects.query_objects_with_config.keys()
    ])
    studies = ['Study3']
    common_reports_query_objects.filter_query_objects(studies)

    study_wrapper, config = \
        list(common_reports_query_objects.query_objects_with_config.items())[0]
    assert study_wrapper is not None
    assert config is not None

    common_report = CommonReport(
        study_wrapper, 
        config.filter_info, 
        config.phenotypes_info, 
        config.effect_groups,
        config.effect_types)

    assert common_report is not None
    pprint(common_report.to_dict())

    assert common_report.denovo_report is not None
    assert len(common_report.denovo_report.tables) == 3

    table0 = common_report.denovo_report.tables[0]
    rows0 = table0.rows
    assert len(rows0) == 2
    row0 = rows0[0]
    row1 = rows0[1]
    pprint(row0.to_dict())
    pprint(row1.to_dict())

    assert row0.effect_type == 'Frame-shift'
    assert len(row0.row) == 1

    cell0 = row0.row[0]
    assert cell0.number_of_observed_events == 1
    assert cell0.number_of_children_with_event == 1

    assert row1.effect_type == 'Missense'
    assert len(row1.row) == 1

    cell0 = row1.row[0]
    assert cell0.number_of_observed_events == 2
    assert cell0.number_of_children_with_event == 1


