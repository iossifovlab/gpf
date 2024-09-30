# pylint: disable=W0621,C0114,C0116,W0212,W0613

import json
from urllib.parse import urlencode

import pytest
from rest_framework import status  # type: ignore

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


def name_in_gene_sets(gene_sets, name, count=None):
    for gene_set in gene_sets:
        if gene_set["name"] == name:
            print(gene_set)
            if count is not None:
                if gene_set["count"] == count:
                    return True
                return False
            return True

    return False


def test_gene_sets_collections(db, admin_client):
    url = "/api/v3/gene_sets/gene_sets_collections"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK, repr(response.content)

    data = response.data

    local_main = data[0]
    assert local_main["name"] == "main"
    denovo = data[1]
    assert denovo["name"] == "denovo"
    local_mapping = data[2]
    assert local_mapping["name"] == "test_mapping"
    local_gmt = data[3]
    assert local_gmt["name"] == "test_gmt"

    print(data)
    assert len(data) == 4, data


def test_gene_set_download(db, admin_client, wdae_gpf_instance):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "denovo",
        "geneSet": "Synonymous",
        "geneSetsTypes": {
            "f1_trio": {"phenotype": ["phenotype1", "unaffected"]},
        },
    }

    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json",
    )

    assert response.status_code == status.HTTP_200_OK, repr(response.content)

    result = list(response.streaming_content)

    count = len(result)
    assert count == 1 + 2


@pytest.mark.xfail(reason="[gene models] wrong annotation")
def test_gene_set_download_synonymous_recurrent(db, admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "denovo",
        "geneSet": "Synonymous.Recurrent",
        "geneSetsTypes": {"f2_group": {"phenotype": ["autism"]}},
    }
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json",
    )
    assert response.status_code == status.HTTP_200_OK, repr(response.content)
    result = list(response.streaming_content)
    count = len(result)
    assert count == 1 + 1


def test_denovo_gene_set_not_found(db, admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "denovo",
        "geneSet": "Synonymous.BadBad",
        "geneSetsTypes": {"f1_group": {"phenotype": ["autism"]}},
    }
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json",
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, repr(response)


def test_main_gene_set_not_found(db, admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "main",
        "geneSet": "BadBadName",
    }
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json",
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, repr(response)


def test_bad_gene_set_collection_not_found(db, admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "BadBadName",
        "geneSet": "BadBadName",
    }
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json",
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, repr(response)


@pytest.mark.xfail(reason="[gene models] wrong annotation")
def test_get_gene_set_download_synonymous_autism(db, admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "denovo",
        "geneSet": "Synonymous",
        "geneSetsTypes": {"f1_group": {"phenotype": ["autism"]}},
    }
    request = f"{url}?{urlencode(query)}"
    response = admin_client.get(request)
    assert response.status_code == status.HTTP_200_OK, repr(response.content)
    result = list(response.streaming_content)
    count = len(result)
    # self.assertEqual(546 + 1, count)
    assert count == 1 + 1


@pytest.mark.xfail(reason="[gene models] wrong annotation")
def test_get_gene_set_download_synonymous_recurrent(db, admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "denovo",
        "geneSet": "Synonymous.Recurrent",
        "geneSetsTypes": {"f2_group": {"phenotype": ["autism"]}},
    }
    request = f"{url}?{urlencode(query)}"
    response = admin_client.get(request)
    assert response.status_code == status.HTTP_200_OK, repr(response.content)
    result = list(response.streaming_content)
    count = len(result)
    assert count == 1 + 1


@pytest.mark.xfail(reason="[gene models] wrong annotation")
def test_get_gene_set_download_synonymous_triple(db, admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "denovo",
        "geneSet": "Synonymous.Triple",
        "geneSetsTypes": {"f3_group": {"phenotype": ["autism"]}},
    }
    request = f"{url}?{urlencode(query)}"
    response = admin_client.get(request)
    assert response.status_code == status.HTTP_200_OK, repr(response.content)
    result = list(response.streaming_content)
    count = len(result)
    assert count == 1 + 1


def test_get_denovo_gene_set_not_found(db, admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "denovo",
        "geneSet": "Synonymous.BadBad",
        "geneSetsTypes": {"f1_group": {"phenotype": ["autism"]}},
    }
    request = f"{url}?{urlencode(query)}"
    response = admin_client.get(request)
    assert response.status_code == status.HTTP_404_NOT_FOUND, repr(response)


def test_get_main_gene_set_not_found(db, admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "main",
        "geneSet": "BadBadName",
    }
    request = f"{url}?{urlencode(query)}"
    response = admin_client.get(request)
    assert response.status_code == status.HTTP_404_NOT_FOUND, repr(response)


def test_get_bad_gene_set_collection_not_found(db, admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "BadBadName",
        "geneSet": "BadBadName",
    }
    request = f"{url}?{urlencode(query)}"
    response = admin_client.get(request)
    assert response.status_code == status.HTTP_404_NOT_FOUND, repr(response)


def test_get_gene_set_collection_empty_query(db, admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {}
    request = f"{url}?{urlencode(query)}"
    response = admin_client.get(request)
    assert response.status_code == status.HTTP_400_BAD_REQUEST, repr(response)


@pytest.mark.xfail(reason="[gene models] wrong annotation")
def test_gene_sets(db, admin_client):
    url = "/api/v3/gene_sets/gene_sets"
    query = {
        "geneSetsCollection": "denovo",
        "geneSetsTypes": {"f1_group": {"phenotype": ["autism"]}},
    }
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json",
    )
    assert response.status_code == status.HTTP_200_OK, repr(response.content)
    result = response.data
    assert name_in_gene_sets(result, "Synonymous", 1)


def test_gene_sets_empty_query(db, admin_client):
    url = "/api/v3/gene_sets/gene_sets"
    query = {}
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST, repr(
        response.content,
    )


def test_gene_sets_missing(db, admin_client):
    url = "/api/v3/gene_sets/gene_sets"
    query = {"geneSetsCollection": "BadBadName"}
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json",
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, repr(
        response.content,
    )
