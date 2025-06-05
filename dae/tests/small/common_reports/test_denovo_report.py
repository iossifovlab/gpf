# pylint: disable=W0621,C0114,C0116,W0212,W0613

from typing import cast

from dae.common_reports.denovo_report import (
    DenovoReport,
    DenovoReportTable,
    EffectCell,
    EffectRow,
)
from dae.person_sets import PersonSet, PersonSetCollection
from dae.studies.study import GenotypeData
from dae.variants.family_variant import FamilyAllele, FamilyVariant


def test_denovo_report_table(
    t4c8_dataset_denovo: list[FamilyVariant],
    phenotype_role_collection: PersonSetCollection,
) -> None:

    denovo_report_table = DenovoReportTable.from_variants(
        t4c8_dataset_denovo,
        ["Missense", "Splice-site"],
        ["Frame-shift", "Nonsense"],
        phenotype_role_collection,
    )
    assert denovo_report_table.group_name == "Phenotype"
    assert sorted(denovo_report_table.columns) == \
        ["autism (2)", "unaffected (2)"]

    assert denovo_report_table.effect_groups == ["Missense"]
    assert denovo_report_table.effect_types == ["Frame-shift"]
    assert len(denovo_report_table.rows) == 2

    assert denovo_report_table.is_empty() is False

    assert len(denovo_report_table.to_dict()) == 5


def test_denovo_report(
    t4c8_dataset: GenotypeData,
    phenotype_role_collection: PersonSetCollection,
) -> None:

    denovo_report = DenovoReport.from_genotype_study(
        t4c8_dataset,
        [phenotype_role_collection],
    )

    assert len(denovo_report.tables) == 1

    assert denovo_report.is_empty() is False

    assert len(denovo_report.to_dict()) == 1
    print(denovo_report.to_dict())


def test_denovo_report_empty(
    t4c8_study_3: GenotypeData,
    phenotype_role_collection: PersonSetCollection,
) -> None:
    denovo_report = DenovoReport.from_genotype_study(
        t4c8_study_3, [phenotype_role_collection],
    )

    assert len(denovo_report.tables) == 0

    assert denovo_report.is_empty() is True

    assert len(denovo_report.to_dict()) == 1


def test_effect_row(
    t4c8_dataset_denovo: list[FamilyVariant],
    phenotype_role_sets: list[PersonSet],
) -> None:
    effect_row = EffectRow(
        "Missense", phenotype_role_sets,
    )
    for fv in t4c8_dataset_denovo:
        effect_row.count_variant(fv)
    out_dict = effect_row.to_dict()
    assert out_dict["effect_type"] == "Missense"

    assert out_dict["row"][0] == {
        "number_of_observed_events": 1,
        "number_of_children_with_event": 1,
        "observed_rate_per_child": 0.5,
        "percent_of_children_with_events": 0.5,
        "column": "autism (2)",
    }
    assert out_dict["row"][1] == {
        "number_of_observed_events": 0,
        "number_of_children_with_event": 0,
        "observed_rate_per_child": 0,
        "percent_of_children_with_events": 0,
        "column": "epilepsy (2)",
    }
    assert out_dict["row"][2] == {
        "number_of_observed_events": 1,
        "number_of_children_with_event": 1,
        "observed_rate_per_child": 0.5,
        "percent_of_children_with_events": 0.5,
        "column": "unaffected (2)",
    }
    assert out_dict["row"][3] == {
        "number_of_observed_events": 0,
        "number_of_children_with_event": 0,
        "observed_rate_per_child": 0,
        "percent_of_children_with_events": 0,
        "column": "unspecified (1)",
    }


def test_effect_cell(
    t4c8_dataset_denovo: list[FamilyVariant],
    phenotype_role_sets: list[PersonSet],
) -> None:
    effect_cell1 = EffectCell(
        phenotype_role_sets[0], "Missense",
    )
    for fv in t4c8_dataset_denovo:
        for aa in fv.alt_alleles:
            fa = cast(FamilyAllele, aa)
            effect_cell1.count_variant(fv, fa)
    assert effect_cell1.to_dict() == {
        "number_of_observed_events": 1,
        "number_of_children_with_event": 1,
        "observed_rate_per_child": 0.5,
        "percent_of_children_with_events": 0.5,
        "column": "autism (2)",
    }

    effect_cell2 = EffectCell(
        phenotype_role_sets[1], "Missense",
    )
    for fv in t4c8_dataset_denovo:
        for aa in fv.alt_alleles:
            fa = cast(FamilyAllele, aa)
            effect_cell2.count_variant(fv, fa)
    assert effect_cell2.to_dict() == {
        "number_of_observed_events": 0,
        "number_of_children_with_event": 0,
        "observed_rate_per_child": 0,
        "percent_of_children_with_events": 0,
        "column": "epilepsy (2)",
    }

    effect_cell3 = EffectCell(
        phenotype_role_sets[2], "Missense",
    )
    for fv in t4c8_dataset_denovo:
        for aa in fv.alt_alleles:
            fa = cast(FamilyAllele, aa)
            effect_cell3.count_variant(fv, fa)
    assert effect_cell3.to_dict() == {
        "number_of_observed_events": 1,
        "number_of_children_with_event": 1,
        "observed_rate_per_child": 0.5,
        "percent_of_children_with_events": 0.5,
        "column": "unaffected (2)",
    }

    effect_cell4 = EffectCell(
        phenotype_role_sets[3], "Missense",
    )
    for fv in t4c8_dataset_denovo:
        for aa in fv.alt_alleles:
            fa = cast(FamilyAllele, aa)
            effect_cell4.count_variant(fv, fa)
    assert effect_cell4.to_dict() == {
        "number_of_observed_events": 0,
        "number_of_children_with_event": 0,
        "observed_rate_per_child": 0,
        "percent_of_children_with_events": 0,
        "column": "unspecified (1)",
    }
