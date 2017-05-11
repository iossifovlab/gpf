'''
Created on Jan 4, 2016

@author: lubo
'''
import unittest
from rest_framework import status
import json
from users_api.tests.base_tests import BaseAuthenticatedUserTest


class Test(BaseAuthenticatedUserTest):

    def test_cnv_plus_3(self):
        data = {
            "geneSyms": "PLD5",
            "effectTypes": "CNV+",
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "None",
            "presentInChild": "autism only",
            "gender": "male,female",
        }

        url = '/api/ssc_query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('2', response.data['count'])
        row = response.data['rows'][0]
        pedigree = json.loads(row[-2])
        prb = pedigree[1][2]
        self.assertEqual(3, prb[-1])

    def test_cnv_minus_1(self):
        data = {
            "geneSyms": "NRXN1",
            "effectTypes": "CNV-",
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "None",
            "presentInChild": "autism only",
            "gender": "male,female",
        }

        url = '/api/ssc_query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('3', response.data['count'])
        row = response.data['rows'][0]
        pedigree = json.loads(row[-2])
        prb = pedigree[1][2]
        self.assertEqual(1, prb[-1])

    def test_lgds(self):
        data = {
            "effectTypes": "nonsense,frame-shift,splice-site",
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "None",
            "presentInChild": "autism only",
            "gender": "male,female",
        }

        url = '/api/ssc_query_variants_preview'

        response = self.client.post(url, data, format='json')
        for row in response.data['rows']:
            pedigree = json.loads(row[-2])
            prb = pedigree[1][2]
            self.assertTrue(prb[-1] < 3)

if __name__ == "__main__":
    unittest.main()
