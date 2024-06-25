# pylint: disable=W0621,C0114,C0116,W0212,W0613

import pytest
from django.test.client import Client
from pytest import MonkeyPatch

pytestmark = pytest.mark.usefixtures(
    "gp_wgpf_instance",
)

ROUTE_PREFIX = "/api/v3/gene_profiles"


def test_configuration(admin_client: Client) -> None:
    response = admin_client.get(f"{ROUTE_PREFIX}/single-view/configuration")

    assert response.status_code == 200
    print(response.data)  # type: ignore

    assert len(
        response.data["genomicScores"],  # type: ignore
    ) == 2

    assert len(
        response.data["genomicScores"][0]["scores"],  # type: ignore
    ) == 3
    assert response.data["genomicScores"][0]["category"] == \
        "protection_scores"

    assert len(
        response.data["genomicScores"][1]["scores"],  # type: ignore
    ) == 3
    assert response.data["genomicScores"][1]["category"] == "autism_scores"

    datasets = response.data["datasets"]  # type: ignore
    assert len(datasets) == 1
    assert datasets[0]["id"] == "iossifov_2014"
    assert len(datasets[0]["statistics"]) == 2
    assert len(datasets[0]["personSets"]) == 2
    assert datasets[0]["personSets"] == [
        {
            "id": "autism",
            "displayName": "autism",
            "collectionId": "phenotype",
            "description": "",
            "parentsCount": 0,
            "childrenCount": 11,
            "statistics": [
                {
                    "id": "denovo_noncoding",
                    "displayName": "Noncoding",
                    "effects": ["noncoding"],
                    "category": "denovo",
                },
                {
                    "id": "denovo_missense",
                    "displayName": "Missense",
                    "effects": ["missense"],
                    "category": "denovo",
                },
            ],
        },
        {
            "id": "unaffected",
            "displayName": "unaffected",
            "collectionId": "phenotype",
            "description": "",
            "parentsCount": 22,
            "childrenCount": 10,
            "statistics": [
                {
                    "id": "denovo_noncoding",
                    "displayName": "Noncoding",
                    "effects": ["noncoding"],
                    "category": "denovo",
                },
                {
                    "id": "denovo_missense",
                    "displayName": "Missense",
                    "effects": ["missense"],
                    "category": "denovo",
                },
            ],
        },
    ]


def test_get_statistic(admin_client: Client) -> None:
    response = admin_client.get(f"{ROUTE_PREFIX}/single-view/gene/CHD8")
    assert response.status_code == 200
    print(response.data)  # type: ignore


def test_get_links(admin_client: Client, monkeypatch: MonkeyPatch) -> None:
    """Test gene profile links."""
    response = admin_client.get(f"{ROUTE_PREFIX}/single-view/gene/chd8")
    assert response.status_code == 200
    assert response.data["geneLinks"] == [  # type: ignore
        {
            "name": "Link with prefix",
            "url": "/datasets/CHD8",
        },
        {
            "name": "Link with gene info",
            "url": (
                "https://site.com/CHD8?db=hg19"
                "&position=chr14/21853353-21905457"
            ),
        },
    ]

    monkeypatch.setenv("WDAE_PREFIX", "hg38")
    response = admin_client.get(f"{ROUTE_PREFIX}/single-view/gene/CHD8")
    assert response.status_code == 200
    assert response.data["geneLinks"][0] == {  # type: ignore
        "name": "Link with prefix",
        "url": "hg38/datasets/CHD8",
    }
    print(response.data["geneLinks"])  # type: ignore


def test_get_table_config(admin_client: Client) -> None:
    response = admin_client.get(f"{ROUTE_PREFIX}/table/configuration")
    assert response.status_code == 200
    assert "defaultDataset" in response.data  # type: ignore
    assert "columns" in response.data  # type: ignore
    print(response.data)  # type: ignore


def test_get_statistics(admin_client: Client) -> None:
    response = admin_client.get(f"{ROUTE_PREFIX}/table/rows")
    assert response.status_code == 200
    print(response.data)  # type: ignore


def test_get_gene_symbols(admin_client: Client) -> None:
    response = admin_client.get(f"{ROUTE_PREFIX}/table/gene_symbols")
    assert response.status_code == 200
    assert response.data == ["CHD8"]  # type: ignore


def test_get_nonexisting_gene_symbols(admin_client: Client) -> None:
    response = admin_client.get(
        f"{ROUTE_PREFIX}/table/gene_symbols?symbol=DIABLO",
    )
    assert response.status_code == 200
    assert response.data == []  # type: ignore
