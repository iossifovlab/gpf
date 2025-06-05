# pylint: disable=W0621,C0114,C0116,W0212,W0613
from dae.common_reports.family_report import FamiliesReport
from dae.person_sets import PersonSetCollection
from dae.studies.study import GenotypeDataStudy


def test_families_report(
    t4c8_dataset: GenotypeDataStudy,
    phenotype_role_collection: PersonSetCollection,
) -> None:
    families_report = FamiliesReport.from_study(
        t4c8_dataset, [phenotype_role_collection],
    )
    assert len(families_report.families_counters) == 1
    assert len(families_report.to_dict()) == 1
