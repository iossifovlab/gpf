import pytest

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


def test_scores_created(gene_scores_db):
    assert gene_scores_db is not None


def test_lgd_rank_available(gene_scores_db):
    assert "LGD_rank" in gene_scores_db


def test_get_lgd_rank(gene_scores_db):
    w = gene_scores_db["LGD_rank"]

    assert w is not None
    assert w.min() == pytest.approx(1.0, 0.01)
    assert w.max() == pytest.approx(18394.5, 0.01)


def test_get_genes_by_score(gene_scores_db):
    g = gene_scores_db["LGD_rank"].get_genes(1.5, 5.0)
    assert len(g) == 3

    g = gene_scores_db["LGD_rank"].get_genes(-1, 5.0)
    assert len(g) == 4

    g = gene_scores_db["LGD_rank"].get_genes(1.0, 5.0)
    assert len(g) == 4
