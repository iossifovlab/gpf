from dae.common_reports.family_report import FamiliesReport


def test_families_report(study1, filter_objects, families_groups):
    families_report = FamiliesReport(
        families_groups.keys(), families_groups, filter_objects)
    assert families_report.families_total == 10
    assert len(families_report.people_counters) == 1
    print(families_report.families_counters)

    assert len(families_report.families_counters) == 5

    assert len(families_report.to_dict()) == 3
