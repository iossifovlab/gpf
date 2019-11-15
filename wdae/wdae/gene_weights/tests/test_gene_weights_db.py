import pytest

from gpf_instance.gpf_instance import get_gpf_instance

pytestmark = pytest.mark.usefixtures('mock_gpf_instance')


def test_get_gene_gene_weights_db(db):
    gene_weights_db = get_gpf_instance().gene_weights_db

    assert gene_weights_db is not None

    assert len(gene_weights_db) == 5
