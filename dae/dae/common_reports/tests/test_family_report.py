from dae.common_reports.family_report import FamiliesReport


def test_families_report(study1, phenotype_role_collection):
    families_report = FamiliesReport(
        study1.families, [phenotype_role_collection]
    )
    assert families_report.families_total == 10
    assert len(families_report.families_counters) == 1
    assert len(families_report.to_dict()) == 2
