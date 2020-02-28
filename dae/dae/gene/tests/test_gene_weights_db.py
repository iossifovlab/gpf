def test_weights_default(gene_weights_db):
    assert gene_weights_db is not None


def test_weights_rvis_rank(gene_weights_db):
    assert gene_weights_db["RVIS_rank"] is not None

    rvis = gene_weights_db["RVIS_rank"]
    assert rvis.df is not None

    assert "RVIS_rank" in rvis.df.columns


def test_weights_has_rvis_rank(gene_weights_db):
    assert "RVIS_rank" in gene_weights_db


def test_loaded_weights(gene_weights_db):
    assert len(gene_weights_db) == 5
