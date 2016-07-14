'''
Created on Jul 14, 2016

@author: lubo
'''

from rest_framework.test import APITestCase
from rest_framework import status


class Test(APITestCase):

    def test_enrichment_background_models(self):
        url = '/api/v2/enrichment/models/background'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.data)

    def test_enrichment_counting_models(self):
        url = '/api/v2/enrichment/models/counting'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.data)

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
            'enrichmentBackgroundModel': 'synonymousBackgroundModel',
        }
        url = '/api/v2/enrichment/test'

        response = self.client.get(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_enrichment_coding_length_background_model_test(self):
        data = {
            "denovoStudies": "ALL WHOLE EXOME",
            'geneSyms': '',
            'geneStudy': '',
            'transmittedStudies': 'w1202s766e611',
            'geneTerm': 'ChromatinModifiers',
            'geneSet': 'main',
            'enrichmentBackgroundModel': 'codingLenBackgroundModel',
        }
        url = '/api/v2/enrichment/test'

        response = self.client.get(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_enrichment_counting_model_test(self):
        data = {
            "denovoStudies": "ALL WHOLE EXOME",
            'geneSyms': '',
            'geneStudy': '',
            'transmittedStudies': 'w1202s766e611',
            'geneTerm': 'ChromatinModifiers',
            'geneSet': 'main',
            'enrichmentCountingModel': 'enrichmentGeneCounting',
        }
        url = '/api/v2/enrichment/test'

        response = self.client.get(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_enrichment_events_counting_model_test(self):
        data = {
            "denovoStudies": "ALL WHOLE EXOME",
            'geneSyms': '',
            'geneStudy': '',
            'transmittedStudies': 'w1202s766e611',
            'geneTerm': 'ChromatinModifiers',
            'geneSet': 'main',
            'enrichmentCountingModel': 'enrichmentEventsCounting',
        }
        url = '/api/v2/enrichment/test'

        response = self.client.get(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
