'''
Created on Aug 2, 2016

@author: lubo
'''
from rest_framework.test import APITestCase
from rest_framework import status


class Test(APITestCase):

    def test_enrichment_test(self):
        data = {
            "denovoStudies": "ALL WHOLE EXOME",
            'geneSyms': '',
            'geneStudy': '',
            'transmittedStudies': 'w1202s766e611',
            'geneTerm': 'ChromatinModifiers',
            'geneSet': 'main',
        }
        url = '/api/v2/enrichment/test'

        response = self.client.get(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_enrichment_background_model_test(self):
        data = {
            "denovoStudies": "ALL WHOLE EXOME",
            'geneSyms': '',
            'geneStudy': '',
            'transmittedStudies': 'w1202s766e611',
            'geneTerm': 'ChromatinModifiers',
            'geneSet': 'main',
            'enrichmentBackgroundModel': 'samochaBackgroundModel',
        }
        url = '/api/v2/enrichment/test'

        response = self.client.get(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
