import pytest

pytestmark = pytest.mark.usefixtures("wdae_gpf_instance")


def test_get_gene_gene_weights_db(db, wdae_gpf_instance):
    gene_weights_db = wdae_gpf_instance.gene_weights_db

    assert gene_weights_db is not None

    assert len(gene_weights_db) == 5
