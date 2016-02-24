'''
Created on Feb 23, 2016

@author: lubo
'''
from rest_framework.test import APITestCase


class Test(APITestCase):

    def test_gene_weights_partitions(self):
        url = "/api/v2/pheno_reports/measure_partitions"
        data = {
            "measure": "non_verbal_iq",
            "min": 9,
            "max": 40,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        print(response.data)
        self.assertIn('measure',  response.data)
        self.assertEqual('non_verbal_iq', response.data['measure'])

        self.assertIn('left', response.data)
        left = response.data['left']
        self.assertIn('count', left)
        self.assertEqual(0, left['count'])

        self.assertIn('mid', response.data)
        mid = response.data['mid']
        self.assertIn('count', mid)
        self.assertEqual(223, mid['count'])
