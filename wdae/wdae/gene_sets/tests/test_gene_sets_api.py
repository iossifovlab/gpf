import pytest

from urllib.parse import urlencode
from rest_framework import status

import json

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


def name_in_gene_sets(gene_sets, name, count=None):
    for gene_set in gene_sets:
        if gene_set["name"] == name:
            print(gene_set)
            if count is not None:
                if gene_set["count"] == count:
                    return True
                else:
                    return False
            return True

    return False


def test_gene_sets_collections(db, admin_client):
    url = "/api/v3/gene_sets/gene_sets_collections"
    response = admin_client.get(url,)
    assert status.HTTP_200_OK == response.status_code, repr(response.content)

    data = response.data
    assert len(data) == 10

    local_main = data[0]
    assert "main" == local_main["name"]
    denovo = data[1]
    assert "denovo" == denovo["name"]
    remote_denovo = data[2]
    assert "TEST_REMOTE_denovo" == remote_denovo["name"]
    remote_main = data[3]
    assert "TEST_REMOTE_main" == remote_main["name"]
    # self.assertEquals(8, len(denovo['types']))


def test_gene_set_download(db, admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "denovo",
        "geneSet": "Synonymous",
        "geneSetsTypes": {
            "f1_group": {"phenotype": ["phenotype1", "unaffected"]}
        },
    }
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json"
    )

    assert status.HTTP_200_OK == response.status_code, repr(response.content)

    result = list(response.streaming_content)

    count = len(result)
    assert 1 + 1 == count


@pytest.mark.xfail(reason="[gene models] wrong annotation")
def test_gene_set_download_synonymous_recurrent(db, admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "denovo",
        "geneSet": "Synonymous.Recurrent",
        "geneSetsTypes": {"f2_group": {"phenotype": ["autism"]}},
    }
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json"
    )
    assert status.HTTP_200_OK == response.status_code, repr(response.content)
    result = list(response.streaming_content)
    count = len(result)
    assert 1 + 1 == count


def test_denovo_gene_set_not_found(db, admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "denovo",
        "geneSet": "Synonymous.BadBad",
        "geneSetsTypes": {"f1_group": {"phenotype": ["autism"]}},
    }
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json"
    )
    assert status.HTTP_404_NOT_FOUND == response.status_code, repr(response)


def test_main_gene_set_not_found(db, admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "main",
        "geneSet": "BadBadName",
    }
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json"
    )
    assert status.HTTP_404_NOT_FOUND == response.status_code, repr(response)


def test_bad_gene_set_collection_not_found(db, admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "BadBadName",
        "geneSet": "BadBadName",
    }
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json"
    )
    assert status.HTTP_404_NOT_FOUND == response.status_code, repr(response)


@pytest.mark.xfail(reason="[gene models] wrong annotation")
def test_get_gene_set_download_synonymous_autism(db, admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "denovo",
        "geneSet": "Synonymous",
        "geneSetsTypes": {"f1_group": {"phenotype": ["autism"]}},
    }
    request = "{}?{}".format(url, urlencode(query))
    response = admin_client.get(request)
    assert status.HTTP_200_OK == response.status_code, repr(response.content)
    result = list(response.streaming_content)
    count = len(result)
    # self.assertEqual(546 + 1, count)
    assert 1 + 1 == count


@pytest.mark.xfail(reason="[gene models] wrong annotation")
def test_get_gene_set_download_synonymous_recurrent(db, admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "denovo",
        "geneSet": "Synonymous.Recurrent",
        "geneSetsTypes": {"f2_group": {"phenotype": ["autism"]}},
    }
    request = "{}?{}".format(url, urlencode(query))
    response = admin_client.get(request)
    assert status.HTTP_200_OK == response.status_code, repr(response.content)
    result = list(response.streaming_content)
    count = len(result)
    assert 1 + 1 == count


@pytest.mark.xfail(reason="[gene models] wrong annotation")
def test_get_gene_set_download_synonymous_triple(db, admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "denovo",
        "geneSet": "Synonymous.Triple",
        "geneSetsTypes": {"f3_group": {"phenotype": ["autism"]}},
    }
    request = "{}?{}".format(url, urlencode(query))
    response = admin_client.get(request)
    assert status.HTTP_200_OK == response.status_code, repr(response.content)
    result = list(response.streaming_content)
    count = len(result)
    assert 1 + 1 == count


def test_get_denovo_gene_set_not_found(db, admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "denovo",
        "geneSet": "Synonymous.BadBad",
        "geneSetsTypes": {"f1_group": {"phenotype": ["autism"]}},
    }
    request = "{}?{}".format(url, urlencode(query))
    response = admin_client.get(request)
    assert status.HTTP_404_NOT_FOUND == response.status_code, repr(response)


def test_get_main_gene_set_not_found(db, admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "main",
        "geneSet": "BadBadName",
    }
    request = "{}?{}".format(url, urlencode(query))
    response = admin_client.get(request)
    assert status.HTTP_404_NOT_FOUND == response.status_code, repr(response)


def test_get_bad_gene_set_collection_not_found(db, admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "BadBadName",
        "geneSet": "BadBadName",
    }
    request = "{}?{}".format(url, urlencode(query))
    response = admin_client.get(request)
    assert status.HTTP_404_NOT_FOUND == response.status_code, repr(response)


def test_get_gene_set_collection_empty_query(db, admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {}
    request = "{}?{}".format(url, urlencode(query))
    response = admin_client.get(request)
    assert status.HTTP_400_BAD_REQUEST == response.status_code, repr(response)


@pytest.mark.xfail(reason="[gene models] wrong annotation")
def test_gene_sets(db, admin_client):
    url = "/api/v3/gene_sets/gene_sets"
    query = {
        "geneSetsCollection": "denovo",
        "geneSetsTypes": {"f1_group": {"phenotype": ["autism"]}},
    }
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json"
    )
    assert status.HTTP_200_OK == response.status_code, repr(response.content)
    result = response.data
    assert name_in_gene_sets(result, "Synonymous", 1)


def test_gene_sets_empty_query(db, admin_client):
    url = "/api/v3/gene_sets/gene_sets"
    query = {}
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json"
    )
    assert status.HTTP_400_BAD_REQUEST == response.status_code, repr(
        response.content
    )


def test_gene_sets_missing(db, admin_client):
    url = "/api/v3/gene_sets/gene_sets"
    query = {"geneSetsCollection": "BadBadName"}
    response = admin_client.post(
        url, json.dumps(query), content_type="application/json", format="json"
    )
    assert status.HTTP_404_NOT_FOUND == response.status_code, repr(
        response.content
    )


def test_gene_sets_remote(db, admin_client):
    url = "/api/v3/gene_sets/gene_sets"
    query = {"geneSetsCollection": "TEST_REMOTE_main"}
    response = admin_client.post(
        url, query, content_type="application/json", format="json"
    )

    assert response.status_code == status.HTTP_200_OK
    print(response.data)
    assert len(response.data) == 15
    checked = 0
    for gs in response.data:
        if gs["name"] == "chromatin modifiers":
            assert gs["count"] == 428
            checked += 1
        if gs["name"] == "CHD8 target genes":
            assert gs["count"] == 2158
            checked += 1
        if gs["name"] == "autism candidates from Iossifov PNAS 2015":
            assert gs["count"] == 239
            checked += 1

    assert checked == 3


def test_gene_sets_remote_download(db, admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "TEST_REMOTE_main",
        "geneSet": "PSD",
    }
    response = admin_client.get(
        url, query, content_type="application/json", format="json"
    )

    assert response.status_code == status.HTTP_200_OK
    print(list(response.streaming_content))


def test_denovo_gene_sets_remote(db, admin_client):
    url = "/api/v3/gene_sets/gene_sets"
    query = {
        "geneSetsCollection": "TEST_REMOTE_denovo",
        "geneSetsTypes": {"iossifov_2014": {"status": ["affected"]}}
    }
    response = admin_client.post(
        url, query, content_type="application/json", format="json"
    )

    assert response.status_code == status.HTTP_200_OK
    print(response.data)
    assert len(response.data) == 16
    lgds = list(filter(lambda x: x["name"] == "LGDs", response.data))[0]
    assert lgds["count"] == 358  # 363


def test_denovo_gene_sets_remote_download(db, admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "TEST_REMOTE_denovo",
        "geneSet": "LGDs",
        "geneSetsTypes": json.dumps(
            {"iossifov_2014": {"status": ["affected"]}}
        )
    }
    response = admin_client.get(
        url, query, content_type="application/json", format="json"
    )

    assert response.status_code == status.HTTP_200_OK
    print(list(response.streaming_content))
