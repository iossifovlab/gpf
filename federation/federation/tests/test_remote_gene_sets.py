# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from federation.gene_sets_db import RemoteGeneSetCollection
from federation.rest_api_client import RESTClient


@pytest.mark.skip
def test_get_gene_set(rest_client: RESTClient) -> None:
    rgsc = RemoteGeneSetCollection(
        "main", rest_client, "", "",
    )
    gene_set = rgsc.get_gene_set("CHD8 target genes")
    assert gene_set is not None

    assert gene_set["name"] == "CHD8 target genes"
    assert gene_set["desc"] == (
        "Cotney J, et al. "
        "The autism-associated chromatin modifier"
        " CHD8 regulates other autism risk genes during human"
        " neurodevelopment. Nat Commun. (2015)"
    )

    assert gene_set["count"] == 2158
    assert len(gene_set["syms"]) == 2158
