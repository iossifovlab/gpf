from dae.common_reports.family_report import FamiliesReport


def test_families_report(study1, phenotype_role_collection):
    families_report = FamiliesReport.from_genotype_study(
        study1, [phenotype_role_collection]
    )
    assert len(families_report.families_counters) == 1
    assert len(families_report.to_dict()) == 1
