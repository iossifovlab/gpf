'''
Created on Jul 1, 2015

@author: lubo
'''
import unittest
from rest_framework.test import APITestCase
import urllib
from rest_framework import status

class Test(APITestCase):


    def setUp(self):
        APITestCase.setUp(self)

    def tearDown(self):
        APITestCase.tearDown(self)

    def test_call_gene_set_download_status(self):
        data = {'gene_set':'main', 'gene_name': 'ChromatinModifiers'}
        url = '/api/gene_set_download?{}'.format(urllib.urlencode(data))
        response = self.client.get(url)
        
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        
    def test_call_gene_set_download_content(self):
        data = {'gene_set':'main', 'gene_name': 'ChromatinModifiers'}
        url = '/api/gene_set_download?{}'.format(urllib.urlencode(data))
        response = self.client.get(url)
        
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        count = len(list(response.streaming_content))
        self.assertEqual(428, count)


    def test_gene_set_download_denovo_single_pheno(self):
        data = {'gene_set':'denovo', 
                'gene_set_phenotype': 'autism',
                'gene_name': 'LGDs'}
        
        url = '/api/gene_set_download?{}'.format(urllib.urlencode(data))
        response = self.client.get(url)
        
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        count = len(list(response.streaming_content))
        self.assertEqual(514, count)

    def test_gene_set_download_denovo_double_pheno(self):
        data = {'gene_set':'denovo', 
                'gene_set_phenotype': 'autism,unaffected',
                'gene_name': 'LGDs'}
        
        url = '/api/gene_set_download?{}'.format(urllib.urlencode(data))
        response = self.client.get(url)
        
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        count = len(list(response.streaming_content))
        self.assertEqual(689, count)

    def test_gene_set_download_denovo_triple_pheno(self):
        data = {'gene_set':'denovo', 
                'gene_set_phenotype': 'autism,epilepsy,unaffected',
                'gene_name': 'LGDs'}
        
        url = '/api/gene_set_download?{}'.format(urllib.urlencode(data))
        response = self.client.get(url)
        
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        count = len(list(response.streaming_content))
        self.assertEqual(719, count)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()