'''
Created on Mar 30, 2017

@author: lubo
'''


from rest_framework.test import APITestCase
from rest_framework import status


class Test(APITestCase):

    URL = "/api/v3/measures/partitions"

    def test_non_verbal_iq_partitions(self):
        data = {
            "datasetId": "SSC",
            "measure": "pheno_common.non_verbal_iq",
            "min": 9,
            "max": 40,
        }
        response = self.client.post(self.URL, data, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        data = response.data
        {
            'right': {
                'count': 2539,
                'percent': 0.9189287006876583
            },
            'min': 9.0,
            'max': 40.0,
            'mid': {
                'count': 224,
                'percent': 0.08107129931234165
            },
            'measure': u'pheno_common.non_verbal_iq',
            'left': {
                'count': 0,
                'percent': 0.0
            }
        }
        self.assertIn('right', data)
        self.assertIn('left', data)
        self.assertIn('mid', data)

        self.assertEquals(
            u'pheno_common.non_verbal_iq',
            data['measure']
        )

        self.assertEquals(
            2539,
            data['right']['count']
        )
        self.assertEquals(
            224,
            data['mid']['count']
        )
