# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from gpf_instance.gpf_instance import WGPFInstance

pytestmark = pytest.mark.usefixtures("wdae_gpf_instance")


@pytest.mark.django_db
def test_get_gene_gene_scores_db(
    wdae_gpf_instance: WGPFInstance
) -> None:
    gene_scores_db = wdae_gpf_instance.gene_scores_db

    assert gene_scores_db is not None

    assert len(gene_scores_db) == 5
