# pylint: disable=W0621,C0114,C0116,W0212,W0613
from federation.gene_sets_db import RemoteGeneSetCollection
from federation.rest_api_client import RESTClient


def test_get_all_gene_sets(rest_client: RESTClient) -> None:
    rgsc = RemoteGeneSetCollection(
        "main", rest_client, "", "",
    )

    all_gene_sets = rgsc.get_all_gene_sets()
    assert len(all_gene_sets) == 3

    gene_set_names = [gs.name for gs in all_gene_sets]
    assert gene_set_names == [
        "all_candidates", "c8_candidates", "t4_candidates",
    ]


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
