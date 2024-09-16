# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Any, cast

import pytest

from dae.gene_sets.denovo_gene_sets_db import DenovoGeneSetsDb
from dae.studies.study import GenotypeData

pytestmark = pytest.mark.usefixtures("gene_info_cache_dir", "calc_gene_sets")


def name_in_gene_sets(
    gene_sets: list[dict[str, Any]],
    name: str,
    count: int | None = None,
) -> bool:

    for gene_set in gene_sets:
        if gene_set["name"] == name:
            if count is not None:
                return cast(bool, gene_set["count"] == count)
            return True

    return False


def test_get_all_descriptions(
    t4c8_denovo_gene_sets_db: DenovoGeneSetsDb,
) -> None:
    gene_set_descriptions = t4c8_denovo_gene_sets_db.get_gene_set_descriptions()

    assert gene_set_descriptions["desc"] == "Denovo"
    assert gene_set_descriptions["name"] == "denovo"
    assert gene_set_descriptions["format"] == ["key", " (|count|)"]
    assert len(gene_set_descriptions["types"]) == 4


def test_get_t4c8_study_4_descriptions(
    t4c8_denovo_gene_sets_db: DenovoGeneSetsDb,
) -> None:

    gene_set_descriptions = t4c8_denovo_gene_sets_db.get_gene_set_descriptions(
        permitted_datasets=["t4c8_study_4"],
    )

    assert gene_set_descriptions["desc"] == "Denovo"
    assert gene_set_descriptions["name"] == "denovo"
    assert gene_set_descriptions["format"] == ["key", " (|count|)"]
    assert len(gene_set_descriptions["types"]) == 1
    assert gene_set_descriptions["types"][0]["datasetId"] == "t4c8_study_4"
    assert gene_set_descriptions["types"][0]["datasetName"] == "t4c8_study_4"
    assert gene_set_descriptions["types"][0]["personSetCollectionId"] == \
        "phenotype"
    assert gene_set_descriptions["types"][0]["personSetCollectionName"] == \
        "Phenotype"
    assert len(
        gene_set_descriptions["types"][0]["personSetCollectionLegend"]) == 2


@pytest.mark.parametrize(
    "denovo_gene_set_id,people_groups,count",
    [
        ("Missense", ["autism"], 2),
        ("Missense", ["autism", "unaffected"], 2),
        ("Synonymous", ["autism"], 1),
        ("Synonymous", ["unaffected"], 2),
        ("Synonymous", ["autism", "unaffected"], 2),
    ],
)
def test_get_denovo_gene_set_t4c8_study_4(
    t4c8_denovo_gene_sets_db: DenovoGeneSetsDb,
    denovo_gene_set_id: str,
    people_groups: list[str],
    count: int,
) -> None:
    dgs = t4c8_denovo_gene_sets_db.get_gene_set(
        denovo_gene_set_id, {"t4c8_study_4": {"phenotype": people_groups}},
    )

    assert dgs is not None
    assert dgs["count"] == count
    assert dgs["name"] == denovo_gene_set_id
    assert dgs["desc"] == (
        f"{denovo_gene_set_id} "
        f"(t4c8_study_4:phenotype:{','.join(people_groups)})"
    )


@pytest.mark.parametrize(
    "denovo_gene_set_id,people_groups",
    [
        ("LGDs", ["autism"]),
        ("LGDs", ["unaffected"]),
        ("LGDs", ["autism", "unaffected"]),
        ("Missense.Male", ["unaffected"]),
    ],
)
def test_get_denovo_gene_set_t4c8_study_4_empty(
    t4c8_denovo_gene_sets_db: DenovoGeneSetsDb,
    denovo_gene_set_id: str,
    people_groups: list[str],
) -> None:
    dgs = t4c8_denovo_gene_sets_db.get_gene_set(
        denovo_gene_set_id, {"t4c8_study_4": {"phenotype": people_groups}},
    )

    assert dgs is None


def test_get_denovo_gene_sets_t4c8_study_4_autism(
    t4c8_denovo_gene_sets_db: DenovoGeneSetsDb,
) -> None:
    dgs = t4c8_denovo_gene_sets_db.get_all_gene_sets(
        {"t4c8_study_4": {"phenotype": ["autism"]}},
    )

    assert dgs is not None
    assert len(dgs) == 5
    assert name_in_gene_sets(dgs, "Missense.Female", 2)
    assert name_in_gene_sets(dgs, "Synonymous.Female", 1)
    assert name_in_gene_sets(dgs, "Missense", 2)
    assert name_in_gene_sets(dgs, "Synonymous.Recurrent", 1)
    assert name_in_gene_sets(dgs, "Synonymous", 1)


def test_get_denovo_gene_sets_t4c8_study_4_unaffected(
    t4c8_denovo_gene_sets_db: DenovoGeneSetsDb,
) -> None:
    dgs = t4c8_denovo_gene_sets_db.get_all_gene_sets(
        {"t4c8_study_4": {"phenotype": ["unaffected"]}},
    )

    assert dgs is not None
    assert len(dgs) == 5

    assert name_in_gene_sets(dgs, "Missense.Female", 1)
    assert name_in_gene_sets(dgs, "Synonymous.Female", 1)
    assert name_in_gene_sets(dgs, "Missense", 1)
    assert name_in_gene_sets(dgs, "Synonymous", 2)
    assert name_in_gene_sets(dgs, "Synonymous.Male", 1)


def test_get_denovo_gene_sets_f4_autism_unaffected(
    t4c8_denovo_gene_sets_db: DenovoGeneSetsDb,
) -> None:
    dgs = t4c8_denovo_gene_sets_db.get_all_gene_sets(
        {"t4c8_study_4": {"phenotype": ["autism", "unaffected"]}},
    )

    assert dgs is not None
    assert len(dgs) == 7
    assert name_in_gene_sets(dgs, "Missense.Female", 2)
    assert name_in_gene_sets(dgs, "Synonymous.Female", 1)
    assert name_in_gene_sets(dgs, "Missense", 2)
    assert name_in_gene_sets(dgs, "Synonymous.Recurrent", 1)
    assert name_in_gene_sets(dgs, "Missense.Recurrent", 1)
    assert name_in_gene_sets(dgs, "Synonymous", 2)
    assert name_in_gene_sets(dgs, "Synonymous.Male", 1)


def test_all_denovo_gene_set_ids(
    t4c8_denovo_gene_sets_db: DenovoGeneSetsDb,
) -> None:
    assert set(t4c8_denovo_gene_sets_db.get_genotype_data_ids()) == {
        "t4c8_study_1", "t4c8_study_2", "t4c8_dataset", "t4c8_study_4",
    }


@pytest.mark.parametrize("query, count", [
    ({}, 7),
    ({"genes": ["t4"]}, 4),
    ({"genes": ["c8"]}, 3),
    ({"effect_types": ["missense"]}, 3),
    ({"effect_types": ["synonymous"]}, 4),
])
def test_check_new_fixtures(
    query: dict,
    count: int,
    t4c8_study_4: GenotypeData,
) -> None:
    assert t4c8_study_4 is not None
    vs = list(t4c8_study_4.query_variants(**query))
    assert len(vs) == count


@pytest.mark.parametrize("gene_set_name, count, genes", [
    ("Synonymous", 2, {"t4", "c8"}),
    ("Missense", 2, {"t4", "c8"}),
    ("Synonymous.Recurrent", 1, {"t4"}),
    ("Missense.Recurrent", 1, {"c8"}),
    ("Synonymous.Female", 1, {"t4"}),
    ("Synonymous.Male", 1, {"c8"}),
    ("Missense.Female", 2, {"c8", "t4"}),
])
def test_get_denovo_gene_sets_f4_autism_unaffected_t4c8(
    t4c8_denovo_gene_sets_db: DenovoGeneSetsDb,
    gene_set_name: str,
    count: int,
    genes: set[str],
) -> None:
    dgs = t4c8_denovo_gene_sets_db.get_all_gene_sets(
        {"t4c8_study_4": {"phenotype": ["autism", "unaffected"]}},
    )

    assert dgs is not None

    assert len(dgs) == 7

    checked = False
    for denovo_gene_set in dgs:
        if denovo_gene_set["name"] == gene_set_name:
            assert denovo_gene_set["count"] == count
            assert set(denovo_gene_set["syms"]) == genes
            checked = True
            break
    assert checked, "condition not checked"
