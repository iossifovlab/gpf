'''
Created on Feb 16, 2017

@author: lubo
'''
import pytest
from django.utils.http import urlencode
from rest_framework import status


pytestmark = pytest.mark.usefixtures("mocked_dataset_config", "datasets_from_fixtures",
    "gene_info_cache_dir")


# class Test(BaseAuthenticatedUserTest):

def test_gene_sets_collections(admin_client):
    url = "/api/v3/gene_sets/gene_sets_collections"
    response = admin_client.get(url,)
    assert status.HTTP_200_OK == response.status_code, repr(response.content)

    data = response.data
    assert 1 == len(data)

    denovo = data[0]
    assert 'denovo' == denovo['name']
    # self.assertEquals(8, len(denovo['types']))


def test_gene_set_download(admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "denovo",
        "geneSet": "Synonymous",
        "geneSetsTypes": {
            "f1": ["autism", "unaffected"]
        }
    }
    response = admin_client.post(url, query, format='json')

    assert status.HTTP_200_OK == response.status_code, repr(response.content)

    result = list(response.streaming_content)
    count = len(result)
    # self.assertEqual(576 + 1, count)
    assert 1 + 1 == count


def test_gene_set_download_synonymous_recurrent(admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "denovo",
        "geneSet": "Synonymous.Recurrent",
        "geneSetsTypes": {
            "f2": ["autism"]
        }
    }
    response = admin_client.post(url, query, format='json')
    assert status.HTTP_200_OK == response.status_code, repr(response.content)
    result = list(response.streaming_content)
    count = len(result)
    assert 1 + 1 == count


def test_denovo_gene_set_not_found(admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "denovo",
        "geneSet": "Synonymous.BadBad",
        "geneSetsTypes": {
            "f1": ["autism"]
        }
    }
    response = admin_client.post(url, query, format='json')
    assert status.HTTP_404_NOT_FOUND == response.status_code, repr(response)


def test_main_gene_set_not_found(admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "main",
        "geneSet": "BadBadName",
    }
    response = admin_client.post(url, query, format='json')
    assert status.HTTP_404_NOT_FOUND == response.status_code, repr(response)


def test_bad_gene_set_collection_not_found(admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "BadBadName",
        "geneSet": "BadBadName",
    }
    response = admin_client.post(url, query, format='json')
    assert status.HTTP_404_NOT_FOUND == response.status_code, repr(response)


def test_get_gene_set_download_synonymous_autism(admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "denovo",
        "geneSet": "Synonymous",
        "geneSetsTypes": {
            "f1": ["autism"]
        }
    }
    request = "{}?{}".format(url, urlencode(query))
    response = admin_client.get(request)
    assert status.HTTP_200_OK == response.status_code, repr(response.content)
    result = list(response.streaming_content)
    count = len(result)
    # self.assertEqual(546 + 1, count)
    assert 1 + 1 == count


def test_get_gene_set_download_synonymous_recurrent(admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "denovo",
        "geneSet": "Synonymous.Recurrent",
        "geneSetsTypes": {
            "f2": ["autism"]
        }
    }
    request = "{}?{}".format(url, urlencode(query))
    response = admin_client.get(request)
    assert status.HTTP_200_OK == response.status_code, repr(response.content)
    result = list(response.streaming_content)
    count = len(result)
    assert 1 + 1 == count


def test_get_gene_set_download_synonymous_triple(admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "denovo",
        "geneSet": "Synonymous.Triple",
        "geneSetsTypes": {
            "f3": ["autism"]
        }
    }
    request = "{}?{}".format(url, urlencode(query))
    response = admin_client.get(request)
    assert status.HTTP_200_OK == response.status_code, repr(response.content)
    result = list(response.streaming_content)
    count = len(result)
    assert 1 + 1 == count


def test_get_denovo_gene_set_not_found(admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "denovo",
        "geneSet": "Synonymous.BadBad",
        "geneSetsTypes": {
            "f1": ["autism"]
        }
    }
    request = "{}?{}".format(url, urlencode(query))
    response = admin_client.get(request)
    assert status.HTTP_404_NOT_FOUND == response.status_code, repr(response)


def test_get_main_gene_set_not_found(admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "main",
        "geneSet": "BadBadName",
    }
    request = "{}?{}".format(url, urlencode(query))
    response = admin_client.get(request)
    assert status.HTTP_404_NOT_FOUND == response.status_code, repr(response)


def test_get_bad_gene_set_collection_not_found(admin_client):
    url = "/api/v3/gene_sets/gene_set_download"
    query = {
        "geneSetsCollection": "BadBadName",
        "geneSet": "BadBadName",
    }
    request = "{}?{}".format(url, urlencode(query))
    response = admin_client.get(request)
    assert status.HTTP_404_NOT_FOUND == response.status_code, repr(response)
