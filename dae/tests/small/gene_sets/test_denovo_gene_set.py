# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest
from dae.gene_sets.denovo_gene_set_collection import DenovoGeneSetCollection


def test_denovo_gene_sets_legend(trios2_dgsc: DenovoGeneSetCollection) -> None:
    assert trios2_dgsc is not None
    legend = trios2_dgsc.get_gene_sets_types_legend()
    assert len(legend) == 3
    assert legend["datasetId"] == "trios2"
    assert legend["datasetName"] == "trios2"
    assert legend["personSetCollections"][0][
        "personSetCollectionId"
    ] == "status"
    assert legend["personSetCollections"][0][
        "personSetCollectionName"
    ] == "Affected Status"
    assert legend["personSetCollections"][0][
        "personSetCollectionLegend"
    ] == [
        {"id": "affected", "name": "affected", "color": "#e35252"},
        {"id": "unaffected", "name": "unaffected", "color": "#ffffff"},
    ]


@pytest.mark.parametrize(
    "denovo_gene_set,people_groups,count",
    [
        ("LGDs", ["affected"], 2),
        ("LGDs.Male", ["affected"], 1),
        ("LGDs.Female", ["affected"], 1),
        ("Missense", ["affected"], 1),
        ("Missense", ["unaffected"], 1),
        ("Missense.Female", ["affected"], 1),
        ("Missense.Female", ["unaffected"], 1),
        ("Missense", ["affected", "unaffected"], 2),
        ("Synonymous", ["affected"], 1),
    ],
)
def test_get_denovo_gene_set(
        trios2_dgsc: DenovoGeneSetCollection,
        denovo_gene_set: str, people_groups: list[str], count: int) -> None:

    dgs = DenovoGeneSetCollection.get_gene_set_from_collections(
        denovo_gene_set, [trios2_dgsc], {"trios2": {"status": people_groups}},
    )

    assert dgs is not None
    assert dgs["count"] == count
    assert dgs["name"] == denovo_gene_set
    assert dgs["desc"] == \
        f"{denovo_gene_set} (trios2:status:{','.join(people_groups)})"
