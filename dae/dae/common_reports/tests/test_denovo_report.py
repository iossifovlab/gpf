from dae.common_reports.denovo_report import \
    DenovoReportTable, \
    DenovoReport, \
    EffectRow, \
    EffectCell


def test_denovo_report_table(denovo_variants_ds1, phenotype_role_collection):

    denovo_report_table = DenovoReportTable.from_variants(
        denovo_variants_ds1,
        ["Missense", "Splice-site"],
        ["Frame-shift", "Nonsense"],
        phenotype_role_collection,
    )

    assert denovo_report_table.group_name == "Diagnosis"
    assert sorted(denovo_report_table.columns) == \
        ["phenotype 1 (6)", "phenotype 2 (2)", ]

    assert denovo_report_table.effect_groups == ["Missense"]
    assert denovo_report_table.effect_types == ["Frame-shift"]
    assert len(denovo_report_table.rows) == 2

    assert denovo_report_table.is_empty() is False

    assert len(denovo_report_table.to_dict()) == 5


def test_denovo_report(
        genotype_data_group1, phenotype_role_collection, denovo_variants_ds1):

    denovo_report = DenovoReport.from_genotype_study(
        genotype_data_group1,
        [phenotype_role_collection],
    )

    # assert denovo_report.denovo_variants == denovo_variants_ds1
    assert len(denovo_report.tables) == 1

    assert denovo_report.is_empty() is False

    assert len(denovo_report.to_dict()) == 1
    print(denovo_report.to_dict())


def test_denovo_report_empty(study2, phenotype_role_collection):
    denovo_report = DenovoReport.from_genotype_study(
        study2, phenotype_role_collection
    )

    assert len(denovo_report.tables) == 0

    assert denovo_report.is_empty() is True

    assert len(denovo_report.to_dict()) == 1


def test_effect_row(denovo_variants_ds1, phenotype_role_sets):
    effect_row = EffectRow(
        denovo_variants_ds1, "Missense", phenotype_role_sets
    )
    out_dict = effect_row.to_dict()
    assert out_dict["effect_type"] == "Missense"
    assert out_dict["row"][0] == {
        "number_of_observed_events": 3,
        "number_of_children_with_event": 3,
        "observed_rate_per_child": 0.5,
        "percent_of_children_with_events": 0.5,
        "column": "phenotype 1 (6)"
    }
    assert out_dict["row"][1] == {
        "number_of_observed_events": 2,
        "number_of_children_with_event": 1,
        "observed_rate_per_child": 1.0,
        "percent_of_children_with_events": 0.5,
        "column": "phenotype 2 (2)"
    }
    assert out_dict["row"][2] == {
        "number_of_observed_events": 0,
        "number_of_children_with_event": 0,
        "observed_rate_per_child": 0,
        "percent_of_children_with_events": 0,
        "column": "unaffected (1)"
    }
    assert out_dict["row"][3] == {
        "number_of_observed_events": 0,
        "number_of_children_with_event": 0,
        "observed_rate_per_child": 0,
        "percent_of_children_with_events": 0,
        "column": "unknown (4)"
    }


def test_effect_cell(denovo_variants_ds1, phenotype_role_sets):
    effect_cell1 = EffectCell(
        denovo_variants_ds1, phenotype_role_sets[0], "Missense"
    )
    assert effect_cell1.to_dict() == {
        "number_of_observed_events": 3,
        "number_of_children_with_event": 3,
        "observed_rate_per_child": 0.5,
        "percent_of_children_with_events": 0.5,
        "column": "phenotype 1 (6)"
    }
    effect_cell2 = EffectCell(
        denovo_variants_ds1, phenotype_role_sets[1], "Missense"
    )
    assert effect_cell2.to_dict() == {
        "number_of_observed_events": 2,
        "number_of_children_with_event": 1,
        "observed_rate_per_child": 1.0,
        "percent_of_children_with_events": 0.5,
        "column": "phenotype 2 (2)"
    }
    effect_cell3 = EffectCell(
        denovo_variants_ds1, phenotype_role_sets[2], "Missense"
    )
    assert effect_cell3.to_dict() == {
        "number_of_observed_events": 0,
        "number_of_children_with_event": 0,
        "observed_rate_per_child": 0,
        "percent_of_children_with_events": 0,
        "column": "unaffected (1)"
    }
    effect_cell4 = EffectCell(
        denovo_variants_ds1, phenotype_role_sets[3], "Missense"
    )
    assert effect_cell4.to_dict() == {
        "number_of_observed_events": 0,
        "number_of_children_with_event": 0,
        "observed_rate_per_child": 0,
        "percent_of_children_with_events": 0,
        "column": "unknown (4)"
    }
