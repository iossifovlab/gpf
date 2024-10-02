# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Any, cast

from dae.gene_sets.denovo_gene_set_collection import DenovoGeneSetCollection


def name_in_gene_sets(
    gene_sets: list[dict[str, Any]],
    name: str,
    count: int | None = None,
) -> bool:
    print(gene_sets)

    for gene_set in gene_sets:
        if gene_set["name"] == name:
            print(gene_set)
            if count is not None:
                return cast(bool, gene_set["count"] == count)
            return True

    return False


def test_generate_cache(
    t4c8_denovo_gene_sets: list[DenovoGeneSetCollection],
) -> None:
    assert len(t4c8_denovo_gene_sets) == 3
    computed = t4c8_denovo_gene_sets[0]

    assert computed is not None


def test_load_cache(
    t4c8_denovo_gene_sets: list[DenovoGeneSetCollection],
) -> None:
    cache = t4c8_denovo_gene_sets[0].cache
    assert cache


def test_t4c8_study_1_autism_get_gene_sets(
    t4c8_denovo_gene_sets: list[DenovoGeneSetCollection],
) -> None:
    gene_sets = DenovoGeneSetCollection.get_all_gene_sets(
        t4c8_denovo_gene_sets,
        denovo_gene_set_spec={"t4c8_study_1": {"phenotype": ["autism"]}},
    )

    assert gene_sets
    assert name_in_gene_sets(gene_sets, "Synonymous", 1)


def test_t4c8_study_1_affected_and_unaffected_get_gene_sets(
    t4c8_denovo_gene_sets: list[DenovoGeneSetCollection],
) -> None:
    gene_sets = DenovoGeneSetCollection.get_all_gene_sets(
        t4c8_denovo_gene_sets,
        denovo_gene_set_spec={
            "t4c8_study_1": {"phenotype": ["autism", "unaffected"]},
        },
    )

    assert gene_sets
    assert name_in_gene_sets(gene_sets, "Synonymous", 2)


def test_t4c8_study_1_unaffected_get_gene_sets(
    t4c8_denovo_gene_sets: list[DenovoGeneSetCollection],
) -> None:
    gene_sets = DenovoGeneSetCollection.get_all_gene_sets(
        t4c8_denovo_gene_sets,
        denovo_gene_set_spec={"t4c8_study_1": {"phenotype": ["unaffected"]}},
    )

    assert gene_sets

    assert name_in_gene_sets(gene_sets, "Missense", 1)
    assert name_in_gene_sets(gene_sets, "Missense.Male", 1)


def test_t4c8_study_1_single_get_gene_sets(
    t4c8_denovo_gene_sets: list[DenovoGeneSetCollection],
) -> None:
    gene_sets = DenovoGeneSetCollection.get_all_gene_sets(
        t4c8_denovo_gene_sets,
        denovo_gene_set_spec={"t4c8_study_1": {"phenotype": ["unaffected"]}},
    )

    assert gene_sets

    assert name_in_gene_sets(gene_sets, "Missense.Single", 1)
    assert name_in_gene_sets(gene_sets, "Missense.Male", 1)


def test_t4c8_study_4_synonymous(
    t4c8_denovo_gene_sets: list[DenovoGeneSetCollection],
) -> None:
    gene_sets = DenovoGeneSetCollection.get_all_gene_sets(
        t4c8_denovo_gene_sets,
        denovo_gene_set_spec={"t4c8_study_4": {"phenotype": ["autism"]}},
    )

    assert gene_sets

    assert name_in_gene_sets(gene_sets, "Synonymous", 1)
    assert name_in_gene_sets(gene_sets, "Synonymous.Recurrent", 1)
    assert name_in_gene_sets(gene_sets, "Synonymous.Triple", 1)


def test_t4c8_study_4_missense(
    t4c8_denovo_gene_sets: list[DenovoGeneSetCollection],
) -> None:
    gene_sets = DenovoGeneSetCollection.get_all_gene_sets(
        t4c8_denovo_gene_sets,
        denovo_gene_set_spec={"t4c8_study_4": {"phenotype": ["unaffected"]}},
    )

    assert gene_sets

    assert name_in_gene_sets(gene_sets, "Missense", 1)
    assert not name_in_gene_sets(gene_sets, "Missense.Recurrent")
    assert not name_in_gene_sets(gene_sets, "Missense.Triple")
