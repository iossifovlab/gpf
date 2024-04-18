# pylint: disable=W0621,C0114,C0116,W0212,W0613

from typing import List, cast

from dae.common_reports.denovo_report import (
    DenovoReport,
    DenovoReportTable,
    EffectCell,
    EffectRow,
)
from dae.person_sets import PersonSet, PersonSetCollection
from dae.studies.study import GenotypeDataGroup, GenotypeDataStudy
from dae.variants.family_variant import FamilyAllele, FamilyVariant


def test_denovo_report_table(
    denovo_variants_ds1: List[FamilyVariant],
    phenotype_role_collection: PersonSetCollection,
) -> None:

    denovo_report_table = DenovoReportTable.from_variants(
        denovo_variants_ds1,
        ["Missense", "Splice-site"],
        ["Frame-shift", "Nonsense"],
        phenotype_role_collection,
    )
    assert denovo_report_table.group_name == "Diagnosis"
    assert sorted(denovo_report_table.columns) == \
        ["phenotype 1 (6)", "phenotype 2 (2)"]

    assert denovo_report_table.effect_groups == ["Missense"]
    assert denovo_report_table.effect_types == ["Frame-shift"]
    assert len(denovo_report_table.rows) == 2

    assert denovo_report_table.is_empty() is False

    assert len(denovo_report_table.to_dict()) == 5


def test_denovo_report(
    genotype_data_group1: GenotypeDataGroup,
    phenotype_role_collection: PersonSetCollection,
    denovo_variants_ds1: List[FamilyVariant],
) -> None:

    denovo_report = DenovoReport.from_genotype_study(
        genotype_data_group1,
        [phenotype_role_collection],
    )

    # assert denovo_report.denovo_variants == denovo_variants_ds1
    assert len(denovo_report.tables) == 1

    assert denovo_report.is_empty() is False

    assert len(denovo_report.to_dict()) == 1
    print(denovo_report.to_dict())


def test_denovo_report_empty(
    study2: GenotypeDataStudy,
    phenotype_role_collection: PersonSetCollection,
) -> None:
    denovo_report = DenovoReport.from_genotype_study(
        study2, [phenotype_role_collection],
    )

    assert len(denovo_report.tables) == 0

    assert denovo_report.is_empty() is True

    assert len(denovo_report.to_dict()) == 1


def test_effect_row(
    denovo_variants_ds1: List[FamilyVariant],
    phenotype_role_sets: List[PersonSet],
) -> None:
    effect_row = EffectRow(
        "Missense", phenotype_role_sets,
    )
    for fv in denovo_variants_ds1:
        effect_row.count_variant(fv)
    out_dict = effect_row.to_dict()
    assert out_dict["effect_type"] == "Missense"

    assert out_dict["row"][0] == {
        "number_of_observed_events": 3,
        "number_of_children_with_event": 3,
        "observed_rate_per_child": 0.5,
        "percent_of_children_with_events": 0.5,
        "column": "phenotype 1 (6)",
    }
    assert out_dict["row"][1] == {
        "number_of_observed_events": 2,
        "number_of_children_with_event": 1,
        "observed_rate_per_child": 1.0,
        "percent_of_children_with_events": 0.5,
        "column": "phenotype 2 (2)",
    }
    assert out_dict["row"][2] == {
        "number_of_observed_events": 0,
        "number_of_children_with_event": 0,
        "observed_rate_per_child": 0,
        "percent_of_children_with_events": 0,
        "column": "unaffected (1)",
    }
    assert out_dict["row"][3] == {
        "number_of_observed_events": 0,
        "number_of_children_with_event": 0,
        "observed_rate_per_child": 0,
        "percent_of_children_with_events": 0,
        "column": "unknown (4)",
    }


def test_effect_cell(
    denovo_variants_ds1: List[FamilyVariant],
    phenotype_role_sets: List[PersonSet],
) -> None:
    effect_cell1 = EffectCell(
        phenotype_role_sets[0], "Missense",
    )
    for fv in denovo_variants_ds1:
        for aa in fv.alt_alleles:
            fa = cast(FamilyAllele, aa)
            effect_cell1.count_variant(fv, fa)
    assert effect_cell1.to_dict() == {
        "number_of_observed_events": 3,
        "number_of_children_with_event": 3,
        "observed_rate_per_child": 0.5,
        "percent_of_children_with_events": 0.5,
        "column": "phenotype 1 (6)",
    }

    effect_cell2 = EffectCell(
        phenotype_role_sets[1], "Missense",
    )
    for fv in denovo_variants_ds1:
        for aa in fv.alt_alleles:
            fa = cast(FamilyAllele, aa)
            effect_cell2.count_variant(fv, fa)
    assert effect_cell2.to_dict() == {
        "number_of_observed_events": 2,
        "number_of_children_with_event": 1,
        "observed_rate_per_child": 1.0,
        "percent_of_children_with_events": 0.5,
        "column": "phenotype 2 (2)",
    }

    effect_cell3 = EffectCell(
        phenotype_role_sets[2], "Missense",
    )
    for fv in denovo_variants_ds1:
        for aa in fv.alt_alleles:
            fa = cast(FamilyAllele, aa)
            effect_cell3.count_variant(fv, fa)
    assert effect_cell3.to_dict() == {
        "number_of_observed_events": 0,
        "number_of_children_with_event": 0,
        "observed_rate_per_child": 0,
        "percent_of_children_with_events": 0,
        "column": "unaffected (1)",
    }

    effect_cell4 = EffectCell(
        phenotype_role_sets[3], "Missense",
    )
    for fv in denovo_variants_ds1:
        for aa in fv.alt_alleles:
            fa = cast(FamilyAllele, aa)
            effect_cell4.count_variant(fv, fa)
    assert effect_cell4.to_dict() == {
        "number_of_observed_events": 0,
        "number_of_children_with_event": 0,
        "observed_rate_per_child": 0,
        "percent_of_children_with_events": 0,
        "column": "unknown (4)",
    }
