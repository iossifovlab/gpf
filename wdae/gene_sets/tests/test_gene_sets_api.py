'''
Created on Feb 16, 2017

@author: lubo
'''

from rest_framework import status
from rest_framework.test import APITestCase
from django.utils.http import urlencode


class Test(APITestCase):

    def test_gene_sets_collections(self):
        url = "/api/v3/gene_sets/gene_sets_collections"
        response = self.client.get(url,)
        self.assertEqual(200, response.status_code)

        data = response.data
        self.assertEquals(8, len(data))

        denovo = data[1]
        self.assertEquals('denovo', denovo['name'])
        self.assertEquals(4, len(denovo['types']))

    def test_gene_set_download(self):
        url = "/api/v3/gene_sets/gene_set_download"
        query = {
            "geneSetsCollection": "denovo",
            "geneSet": "LGDs",
            "geneSetsTypes": {
                "SD": ["autism", "epilepsy"]
            }
        }
        response = self.client.post(url, query, format='json')
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        result = list(response.streaming_content)
        count = len(result)
        self.assertEqual(576 + 1, count)

    def test_gene_set_download_lgds_recurrent(self):
        url = "/api/v3/gene_sets/gene_set_download"
        query = {
            "geneSetsCollection": "denovo",
            "geneSet": "LGDs.Recurrent",
            "geneSetsTypes": {
                "SD": ["autism"]
            }
        }
        response = self.client.post(url, query, format='json')
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        result = list(response.streaming_content)
        count = len(result)
        self.assertEqual(45 + 1, count)

    def test_denovo_gene_set_not_found(self):
        url = "/api/v3/gene_sets/gene_set_download"
        query = {
            "geneSetsCollection": "denovo",
            "geneSet": "LGDs.BadBad",
            "geneSetsTypes": {
                "SD": ["autism"]
            }
        }
        response = self.client.post(url, query, format='json')
        self.assertEquals(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_main_gene_set_not_found(self):
        url = "/api/v3/gene_sets/gene_set_download"
        query = {
            "geneSetsCollection": "main",
            "geneSet": "BadBadName",
        }
        response = self.client.post(url, query, format='json')
        self.assertEquals(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_bad_gene_set_collection_not_found(self):
        url = "/api/v3/gene_sets/gene_set_download"
        query = {
            "geneSetsCollection": "BadBadName",
            "geneSet": "BadBadName",
        }
        response = self.client.post(url, query, format='json')
        self.assertEquals(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_get_gene_set_download(self):
        url = "/api/v3/gene_sets/gene_set_download"
        query = {
            "geneSetsCollection": "denovo",
            "geneSet": "LGDs",
            "geneSetsTypes": {
                "SD": ["autism", "epilepsy"]
            }
        }
        request = "{}?{}".format(url, urlencode(query))
        response = self.client.get(request)
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        result = list(response.streaming_content)
        count = len(result)
        self.assertEqual(576 + 1, count)

    def test_get_gene_set_download_lgds_autism(self):
        url = "/api/v3/gene_sets/gene_set_download"
        query = {
            "geneSetsCollection": "denovo",
            "geneSet": "LGDs",
            "geneSetsTypes": {
                "SD":["autism"]
            }
        }
        request = "{}?{}".format(url, urlencode(query))
        response = self.client.get(request)
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        result = list(response.streaming_content)
        count = len(result)
        self.assertEqual(546 + 1, count)

    def test_get_gene_set_download_lgds_recurrent(self):
        url = "/api/v3/gene_sets/gene_set_download"
        query = {
            "geneSetsCollection": "denovo",
            "geneSet": "LGDs.Recurrent",
            "geneSetsTypes": {
                "SD": ["autism"]
            }
        }
        request = "{}?{}".format(url, urlencode(query))
        response = self.client.get(request)
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        result = list(response.streaming_content)
        count = len(result)
        self.assertEqual(45 + 1, count)

    def test_get_denovo_gene_set_not_found(self):
        url = "/api/v3/gene_sets/gene_set_download"
        query = {
            "geneSetsCollection": "denovo",
            "geneSet": "LGDs.BadBad",
            "geneSetsTypes": {
                "SD": ["autism"]
            }
        }
        request = "{}?{}".format(url, urlencode(query))
        response = self.client.get(request)
        self.assertEquals(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_get_main_gene_set_not_found(self):
        url = "/api/v3/gene_sets/gene_set_download"
        query = {
            "geneSetsCollection": "main",
            "geneSet": "BadBadName",
        }
        request = "{}?{}".format(url, urlencode(query))
        response = self.client.get(request)
        self.assertEquals(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_get_bad_gene_set_collection_not_found(self):
        url = "/api/v3/gene_sets/gene_set_download"
        query = {
            "geneSetsCollection": "BadBadName",
            "geneSet": "BadBadName",
        }
        request = "{}?{}".format(url, urlencode(query))
        response = self.client.get(request)
        self.assertEquals(status.HTTP_404_NOT_FOUND, response.status_code)
