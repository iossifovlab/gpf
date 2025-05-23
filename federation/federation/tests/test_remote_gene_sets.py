# pylint: disable=W0621,C0114,C0116,W0212,W0613
from federation.gene_sets_db import RemoteGeneSetCollection
from federation.rest_api_client import RESTClient


def test_get_gene_set(rest_client: RESTClient) -> None:
    rgsc = RemoteGeneSetCollection(
        "main", rest_client, "", "",
    )
    gene_set = rgsc.get_gene_set("t4_candidates")
    assert gene_set is not None

    assert gene_set["name"] == "t4_candidates"
    assert gene_set["desc"] == "T4 Candidates"

    assert gene_set["count"] == 1
    assert len(gene_set["syms"]) == 1
