def test_scores_default(gene_scores_db):
    assert gene_scores_db is not None


def test_scores_rvis_rank(gene_scores_db):
    assert gene_scores_db["RVIS_rank"] is not None

    rvis = gene_scores_db["RVIS_rank"]
    assert rvis.df is not None

    assert "RVIS_rank" in rvis.df.columns


def test_scores_has_rvis_rank(gene_scores_db):
    assert "RVIS_rank" in gene_scores_db


def test_loaded_scores(gene_scores_db):
    assert len(gene_scores_db) == 2
