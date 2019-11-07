from dae.common_reports.common_report import CommonReport


def test_common_report(study4, study3, common_reports_config):
    common_report = CommonReport(study4, common_reports_config)

    assert common_report.id == 'study4'
    assert common_report.families_report
    assert common_report.denovo_report
    assert common_report.study_name == 'Study4'
    assert sorted(common_report.phenotype) == \
        sorted(['unaffected', 'phenotype1'])
    assert common_report.study_type == 'WE'
    assert common_report.study_year == ''
    assert common_report.pub_med == ''
    assert common_report.families == 3
    assert common_report.number_of_probands == 3
    assert common_report.number_of_siblings == 9
    assert common_report.denovo is True
    assert common_report.transmitted is False
    assert common_report.study_description == 'Study 4'

    assert len(common_report.to_dict()) == 14
