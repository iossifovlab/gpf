'''
Created on Jun 10, 2015

@author: lubo
'''
import unittest
from rest_framework.test import APITestCase
from rest_framework import status


class Test(APITestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def test_denovo_frequencies_not_false(self):

        data = {
            "geneSyms": "PTEN",
            "denovoStudies":"ALL WHOLE EXOME",
            "effectTypes": "Frame-shift",
            "phenoType": "autism",
            "gender": "female,male"
        }

        url = '/api/query_variants_preview'        

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('1', response.data['count'])
        
        print(response.data)
        
        cols = response.data['cols']
        ssc_freq = cols.index('SSCfreq')
        self.assertTrue(ssc_freq > 0)
        rows = response.data['rows']
        
        self.assertNotEqual('False', rows[0][ssc_freq])