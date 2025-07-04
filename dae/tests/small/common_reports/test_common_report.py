# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest_mock
from dae.common_reports.denovo_report import DenovoReport
from dae.studies.study import GenotypeDataStudy


def test_common_report(t4c8_study_4: GenotypeDataStudy) -> None:
    common_report = t4c8_study_4.build_report()

    assert common_report.study_id == "t4c8_study_4"
    assert common_report.families_report
    assert common_report.denovo_report
    assert common_report.study_name == "t4c8_study_4"
    assert common_report.phenotype == ["affected", "unaffected"]
    assert common_report.study_type == "WE"
    assert not common_report.study_year
    assert not common_report.pub_med
    assert common_report.families == 3
    assert common_report.number_of_probands == 3
    assert common_report.number_of_siblings == 2
    assert common_report.denovo is True
    assert common_report.transmitted is True
    assert common_report.study_description is None

    assert len(common_report.to_dict()) == 15
    print(common_report.to_dict())


def test_common_report_empty_denovo(
    t4c8_study_4: GenotypeDataStudy,
    mocker: pytest_mock.MockerFixture,
) -> None:
    denovo_report_mock = mocker.Mock(return_value=DenovoReport({"tables": []}))
    mocker.patch(
        "dae.common_reports.common_report."
        "DenovoReport.from_genotype_study",
        new=denovo_report_mock,
    )

    common_report = t4c8_study_4.build_report()

    assert common_report.study_id == "t4c8_study_4"
    assert common_report.families_report
    assert common_report.denovo_report is not None
    assert common_report.study_name == "t4c8_study_4"
    assert common_report.phenotype == ["affected", "unaffected"]
    assert common_report.study_type == "WE"
    assert not common_report.study_year
    assert not common_report.pub_med
    assert common_report.families == 3
    assert common_report.number_of_probands == 3
    assert common_report.number_of_siblings == 2
    assert common_report.denovo is True
    assert common_report.transmitted is True
    assert common_report.study_description is None

    assert len(common_report.to_dict()) == 15
    assert common_report.to_dict()["denovo_report"] is not None
    print(common_report.to_dict())
