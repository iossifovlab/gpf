# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.gene_sets.denovo_gene_set_collection import DenovoGeneSetCollection

# pytestmark = pytest.mark.usefixtures("gene_info_cache_dir", "calc_gene_sets")
pytestmark = pytest.mark.xfail


def name_in_gene_sets(gene_sets, name, count=None):
    print(gene_sets)
    for gene_set in gene_sets:
        if gene_set["name"] == name:
            print(gene_set)
            if count is not None:
                if gene_set["count"] == count:
                    return True
                return False
            return True

    return False


def test_generate_cache(denovo_gene_sets, calc_gene_sets, gene_info_cache_dir):
    computed = denovo_gene_sets[0]
    assert computed is not None


def test_load_cache(denovo_gene_sets, calc_gene_sets, gene_info_cache_dir):
    loaded = denovo_gene_sets[0].cache
    assert loaded is not None


def test_f1_autism_get_gene_sets(
    denovo_gene_sets, calc_gene_sets, gene_info_cache_dir,
):
    gene_sets = DenovoGeneSetCollection.get_all_gene_sets(
        denovo_gene_sets,
        denovo_gene_set_spec={"f1_group": {"phenotype": ["autism"]}},
    )

    assert gene_sets

    assert name_in_gene_sets(gene_sets, "Synonymous", 1)


def test_f1_affected_and_unaffected_get_gene_sets(
    denovo_gene_sets, calc_gene_sets, gene_info_cache_dir,
):
    gene_sets = DenovoGeneSetCollection.get_all_gene_sets(
        denovo_gene_sets,
        denovo_gene_set_spec={
            "f1_group": {"phenotype": ["autism", "unaffected"]},
        },
    )

    assert gene_sets

    assert name_in_gene_sets(gene_sets, "Synonymous", 1)


def test_f1_unaffected_get_gene_sets(
    denovo_gene_sets, calc_gene_sets, gene_info_cache_dir,
):
    gene_sets = DenovoGeneSetCollection.get_all_gene_sets(
        denovo_gene_sets,
        denovo_gene_set_spec={"f1_group": {"phenotype": ["unaffected"]}},
    )

    assert gene_sets

    assert name_in_gene_sets(gene_sets, "Missense", 2)
    assert name_in_gene_sets(gene_sets, "Missense.Male", 2)
    # assert name_in_gene_sets(gene_sets, 'Missense.Female', 0)


def test_f1_single_get_gene_sets(
    denovo_gene_sets, calc_gene_sets, gene_info_cache_dir,
):
    gene_sets = DenovoGeneSetCollection.get_all_gene_sets(
        denovo_gene_sets,
        denovo_gene_set_spec={"f1_group": {"phenotype": ["unaffected"]}},
    )

    assert gene_sets

    assert name_in_gene_sets(gene_sets, "Missense.Single", 2)
    assert name_in_gene_sets(gene_sets, "Missense.Male", 2)


def test_synonymous_recurrency_get_gene_sets(
    denovo_gene_sets, calc_gene_sets, gene_info_cache_dir,
):
    gene_sets = DenovoGeneSetCollection.get_all_gene_sets(
        denovo_gene_sets,
        denovo_gene_set_spec={"f2_group": {"phenotype": ["autism"]}},
    )

    assert gene_sets

    assert name_in_gene_sets(gene_sets, "Synonymous", 1)
    assert not name_in_gene_sets(gene_sets, "Synonymous.Triple")


def test_missense_recurrency_get_gene_sets(
    denovo_gene_sets, calc_gene_sets, gene_info_cache_dir,
):
    gene_sets = DenovoGeneSetCollection.get_all_gene_sets(
        denovo_gene_sets,
        denovo_gene_set_spec={"f2_group": {"phenotype": ["unaffected"]}},
    )

    assert gene_sets

    assert name_in_gene_sets(gene_sets, "Missense.Recurrent", 2)
    assert not name_in_gene_sets(gene_sets, "Missense.Triple")


def test_synonymous_triple_get_gene_sets(
    denovo_gene_sets, calc_gene_sets, gene_info_cache_dir,
):
    gene_sets = DenovoGeneSetCollection.get_all_gene_sets(
        denovo_gene_sets,
        denovo_gene_set_spec={"f3_group": {"phenotype": ["autism"]}},
    )

    assert gene_sets

    assert name_in_gene_sets(gene_sets, "Synonymous", 1)
    assert name_in_gene_sets(gene_sets, "Synonymous", 1)


def test_missense_triple_get_gene_sets(
    denovo_gene_sets, calc_gene_sets, gene_info_cache_dir,
):
    gene_sets = DenovoGeneSetCollection.get_all_gene_sets(
        denovo_gene_sets,
        denovo_gene_set_spec={"f3_group": {"phenotype": ["unaffected"]}},
    )

    assert gene_sets

    assert name_in_gene_sets(gene_sets, "Missense.Recurrent", 2)
    assert name_in_gene_sets(gene_sets, "Missense.Triple", 2)


def test_missense_triple_get_gene_sets_affected_and_unaffected(
    denovo_gene_sets, calc_gene_sets, gene_info_cache_dir,
):
    gene_sets = DenovoGeneSetCollection.get_all_gene_sets(
        denovo_gene_sets,
        denovo_gene_set_spec={
            "f3_group": {"phenotype": ["autism", "unaffected"]},
        },
    )

    assert gene_sets

    assert name_in_gene_sets(gene_sets, "Missense.Recurrent", 2)
    assert name_in_gene_sets(gene_sets, "Missense.Triple", 2)


def test_autism_trio_get_gene_sets(
    denovo_gene_set_f4, calc_gene_sets, gene_info_cache_dir,
):
    gene_sets = DenovoGeneSetCollection.get_all_gene_sets(
        [denovo_gene_set_f4],
        denovo_gene_set_spec={"f4_trio": {"phenotype": ["autism"]}},
    )

    assert gene_sets

    assert name_in_gene_sets(gene_sets, "Synonymous", 1)
    assert name_in_gene_sets(gene_sets, "Missense", 1)
    assert name_in_gene_sets(gene_sets, "Missense.Recurrent", 1)
    assert name_in_gene_sets(gene_sets, "Missense.Female", 1)


def test_unaffected_trio_get_gene_sets(
    denovo_gene_set_f4, calc_gene_sets, gene_info_cache_dir,
):
    gene_sets = DenovoGeneSetCollection.get_all_gene_sets(
        [denovo_gene_set_f4],
        denovo_gene_set_spec={"f4_trio": {"phenotype": ["unaffected"]}},
    )

    assert gene_sets

    assert name_in_gene_sets(gene_sets, "Synonymous", 1)


def test_affected_and_unaffected_trio_get_gene_sets(
    denovo_gene_set_f4, calc_gene_sets, gene_info_cache_dir,
):
    gene_sets = DenovoGeneSetCollection.get_all_gene_sets(
        [denovo_gene_set_f4],
        denovo_gene_set_spec={
            "f4_trio": {"phenotype": ["autism", "unaffected"]},
        },
    )

    assert gene_sets

    assert name_in_gene_sets(gene_sets, "Synonymous", 2)
    assert name_in_gene_sets(gene_sets, "Missense", 1)
    assert name_in_gene_sets(gene_sets, "Missense.Recurrent", 1)
    assert name_in_gene_sets(gene_sets, "Missense.Female", 1)
