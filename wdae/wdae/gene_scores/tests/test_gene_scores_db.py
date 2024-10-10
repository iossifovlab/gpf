# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from gpf_instance.gpf_instance import WGPFInstance


@pytest.mark.django_db()
def test_get_gene_gene_scores_db(t4c8_wgpf_instance: WGPFInstance) -> None:
    gene_scores_db = t4c8_wgpf_instance.gene_scores_db

    assert gene_scores_db is not None

    assert len(gene_scores_db) == 1
