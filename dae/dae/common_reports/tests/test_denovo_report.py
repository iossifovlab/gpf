from dae.common_reports.denovo_report import \
    DenovoReportTable, \
    DenovoReport


def test_denovo_report_table(
        genotype_data_group1, denovo_variants_ds1, phenotype_role_collection):

    denovo_report_table = DenovoReportTable(
        genotype_data_group1,
        denovo_variants_ds1,
        ["Missense", "Splice-site"],
        ["Frame-shift", "Nonsense"],
        phenotype_role_collection,
    )

    assert denovo_report_table.person_set_collection.name == "Diagnosis"
    assert sorted(denovo_report_table.columns) == sorted(
        ["phenotype 2", "phenotype 1"]
    )
    assert denovo_report_table.effect_groups == ["Missense"]
    assert denovo_report_table.effect_types == ["Frame-shift"]
    assert len(denovo_report_table.rows) == 2

    assert denovo_report_table.is_empty() is False

    assert len(denovo_report_table.to_dict()) == 5


def test_denovo_report(
        genotype_data_group1, phenotype_role_collection, denovo_variants_ds1):

    denovo_report = DenovoReport(
        genotype_data_group1,
        ["Missense"],
        ["Frame-shift"],
        [phenotype_role_collection],
    )

    assert len(denovo_report.denovo_variants) == 8
    # assert denovo_report.denovo_variants == denovo_variants_ds1
    assert len(denovo_report.tables) == 1

    assert denovo_report.is_empty() is False

    assert len(denovo_report.to_dict()) == 1


def test_denovo_report_empty(study2, phenotype_role_collection):
    denovo_report = DenovoReport(
        study2, ["Missense"], ["Frame-shift"], phenotype_role_collection
    )

    assert len(denovo_report.denovo_variants) == 0
    assert denovo_report.denovo_variants == []
    assert len(denovo_report.tables) == 0

    assert denovo_report.is_empty() is True

    assert len(denovo_report.to_dict()) == 1
