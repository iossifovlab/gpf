from dae.common_reports.family_report import FamiliesReport


def test_families_report(study1, filter_objects, families_groups):
    fg = families_groups(study1)
    families_report = FamiliesReport(fg.keys(), fg, filter_objects)
    assert families_report.families_total == 10
    assert len(families_report.people_counters) == 1
    assert len(families_report.families_counters) == 6
    assert len(families_report.to_dict()) == 3
