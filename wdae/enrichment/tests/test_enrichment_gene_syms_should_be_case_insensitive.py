'''
Created on Oct 4, 2016

@author: lubo
'''
from rest_framework import status
from rest_framework.test import APITestCase

import precompute


class Test(APITestCase):

    def test_gene_syms_upper_case(self):

        gene_syms = 'SCNN1D,MEGF6'
        data = {
            "denovoStudies": "ALL WHOLE EXOME",
            'geneSyms': 'SCNN1D,MEGF6',
            'geneStudy': '',
            'transmittedStudies': 'w1202s766e611',
            'geneTerm': '',
            'geneSet': '',
        }
        url = '/api/enrichment_test_by_phenotype'

        response1 = self.client.get(url, data)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        data['geneSyms'] = gene_syms.lower()

        response2 = self.client.get(url, data)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        data1 = response1.data['autism']
        data2 = response2.data['autism']

        self.maxDiff = None
        self.assertEqual(data1, data2)

    def test_mixed_case_gene_syms_upper_case_default_background(self):

        gene_syms = 'C1orf38,C3orf58,OSTalpha,C3orf64'
        data = {
            "denovoStudies": "ALL WHOLE EXOME",
            'geneSyms': gene_syms,
            'geneStudy': '',
            'transmittedStudies': 'w1202s766e611',
            'geneTerm': '',
            'geneSet': '',
        }
        url = '/api/enrichment_test_by_phenotype'

        response1 = self.client.get(url, data)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        data['geneSyms'] = gene_syms.lower()

        response2 = self.client.get(url, data)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        data1 = response1.data['autism']
        data2 = response2.data['autism']

        self.maxDiff = None
        self.assertEqual(data1, data2)

    def test_samocha_background_case_insensitive(self):
        background = precompute.register.get('samochaBackgroundModel')
        self.assertIsNotNone(background.background)

        for gs in background.background['gene']:
            if gs != gs.upper():
                print(gs)
            self.assertEquals(gs, gs.upper())

    def test_synonymous_background_case_insensitive(self):
        background = precompute.register.get('synonymousBackgroundModel')
        for gs in background.background['sym']:
            if gs != gs.upper():
                print(gs)
            self.assertEquals(gs, gs.upper())

    def test_coding_length_background_case_insensitive(self):
        background = precompute.register.get('codingLenBackgroundModel')
        for gs in background.background['sym']:
            if gs != gs.upper():
                print(gs)
            self.assertEquals(gs, gs.upper())

    def test_mixed_case_gene_syms_upper_case_coding_length_background(self):
        gene_syms = 'C1orf38,C3orf58,OSTalpha,C3orf64'
        data = {
            "denovoStudies": "ALL WHOLE EXOME",
            'geneSyms': gene_syms,
            'geneStudy': '',
            'transmittedStudies': 'w1202s766e611',
            'geneTerm': '',
            'geneSet': '',
            'enrichmentBackgroundModel': 'codingLenBackgroundModel',
            'enrichmentCountingModel': 'enrichmentGeneCounting',
        }
        url = '/api/enrichment_test_by_phenotype'

        response1 = self.client.get(url, data)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        data['geneSyms'] = gene_syms.lower()

        response2 = self.client.get(url, data)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        data1 = response1.data['autism']
        data2 = response2.data['autism']

        self.maxDiff = None
        self.assertEqual(data1, data2)

    def test_mixed_case_gene_syms_upper_case_samocha_background(self):
        gene_syms = 'C1orf38,C3orf58,OSTalpha,C3orf64'
        data = {
            "denovoStudies": "ALL WHOLE EXOME",
            'geneSyms': gene_syms,
            'geneStudy': '',
            'transmittedStudies': 'w1202s766e611',
            'geneTerm': '',
            'geneSet': '',
            'enrichmentBackgroundModel': 'samochaBackgroundModel',
            'enrichmentCountingModel': 'enrichmentGeneCounting',
        }
        url = '/api/enrichment_test_by_phenotype'

        response1 = self.client.get(url, data)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        data['geneSyms'] = gene_syms.lower()

        response2 = self.client.get(url, data)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        data1 = response1.data['autism']
        data2 = response2.data['autism']

        self.maxDiff = None
        self.assertEqual(data1, data2)

    def test_mixed_case_gene_syms_upper_case_samocha_background_events(self):
        gene_syms = 'C1orf38,C3orf58,OSTalpha,C3orf64'
        data = {
            "denovoStudies": "ALL WHOLE EXOME",
            'geneSyms': gene_syms,
            'geneStudy': '',
            'transmittedStudies': 'w1202s766e611',
            'geneTerm': '',
            'geneSet': '',
            'enrichmentBackgroundModel': 'samochaBackgroundModel',
            'enrichmentCountingModel': 'enrichmentEventsCounting',
        }
        url = '/api/enrichment_test_by_phenotype'

        response1 = self.client.get(url, data)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        data['geneSyms'] = gene_syms.lower()

        response2 = self.client.get(url, data)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        data1 = response1.data['autism']
        data2 = response2.data['autism']

        self.maxDiff = None
        self.assertEqual(data1, data2)
