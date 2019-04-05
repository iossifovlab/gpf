def test_families_report(families_report):
    assert families_report.families_total == 10
    assert len(families_report.people_counters) == 1
    assert len(families_report.families_counters) == 1

    assert len(families_report.to_dict()) == 3
