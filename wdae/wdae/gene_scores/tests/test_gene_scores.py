# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


def test_scores_created(gene_scores_db):
    assert gene_scores_db is not None


def test_lgd_rank_available(gene_scores_db):
    assert "LGD_rank" in gene_scores_db


def test_get_lgd_rank(gene_scores_db):
    score = gene_scores_db.get_gene_score("gene_scores/LGD")

    assert score is not None
    assert score.get_min("LGD_rank") == pytest.approx(1.0, 0.01)
    assert score.get_max("LGD_rank") == pytest.approx(18394.5, 0.01)


def test_get_genes_by_score(gene_scores_db):
    genes = gene_scores_db.get_gene_score("gene_scores/LGD").get_genes(
        "LGD_rank", 1.5, 5.0
    )
    assert len(genes) == 3

    genes = gene_scores_db.get_gene_score("gene_scores/LGD").get_genes(
        "LGD_rank", -1, 5.0
    )
    assert len(genes) == 4

    genes = gene_scores_db.get_gene_score("gene_scores/LGD").get_genes(
        "LGD_rank", 1.0, 5.0
    )
    assert len(genes) == 4
