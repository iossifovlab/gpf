import pytest

pytestmark = pytest.mark.usefixtures("wdae_gpf_instance")


def test_get_gene_gene_scores_db(db, wdae_gpf_instance):
    gene_scores_db = wdae_gpf_instance.gene_scores_db

    assert gene_scores_db is not None

    assert len(gene_scores_db) == 5
