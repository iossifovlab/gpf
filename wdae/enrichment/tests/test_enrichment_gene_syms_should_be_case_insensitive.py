'''
Created on Oct 4, 2016

@author: lubo
'''
from rest_framework import status
from rest_framework.test import APITestCase


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
