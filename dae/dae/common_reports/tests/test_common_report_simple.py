# pylint: disable=all
# Old, unused test, disable all checks
from pprint import pprint
import pytest

from dae.common_reports.common_report import CommonReport


@pytest.mark.xfail(reason="denovo report reorganized")
def test_common_report_simple(vdb_fixture, common_report_facade):
    assert common_report_facade is not None

    study_wrapper = vdb_fixture.get_wdae_wrapper("Study3")
    assert study_wrapper is not None

    config = common_report_facade.get_common_report_config("Study3")
    assert config is not None
    print(config)

    common_report = CommonReport(study_wrapper, config)

    assert common_report is not None
    assert common_report.id == "Study3"

    print(config.people_groups_info)
    print(config.people_groups)
    print(config.groups)

    assert common_report.denovo_report is not None
    print([t.group_name for t in common_report.denovo_report.tables])

    assert len(common_report.denovo_report.tables) == 1

    table0 = common_report.denovo_report.tables[0]
    rows0 = table0.rows
    assert len(rows0) == 2
    row0 = rows0[0]
    row1 = rows0[1]
    pprint(row0.to_dict())
    pprint(row1.to_dict())

    assert row0.effect_type == "Frame-shift"
    assert len(row0.row) == 2

    cells = sorted(row0.row, key=lambda c: c.column_name)

    cell = cells[0]
    assert cell.column_name == "prb"
    assert cell.number_of_observed_events == 2
    assert cell.number_of_children_with_event == 2

    cell = cells[1]
    assert cell.column_name == "sib"
    assert cell.number_of_observed_events == 0
    assert cell.number_of_children_with_event == 0

    assert row1.effect_type == "Missense"
    assert len(row1.row) == 2

    cells = sorted(row1.row, key=lambda c: c.column)

    cell = cells[0]
    assert cell.column_name == "prb"
    assert cell.number_of_observed_events == 2
    assert cell.number_of_children_with_event == 1

    cell = cells[1]
    assert cell.column_name == "sib"
    assert cell.number_of_observed_events == 1
    assert cell.number_of_children_with_event == 1
