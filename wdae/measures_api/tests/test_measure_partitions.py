'''
Created on Mar 30, 2017

@author: lubo
'''
from __future__ import print_function


from rest_framework.test import APITestCase
from rest_framework import status


class Test(APITestCase):

    URL = "/api/v3/measures/partitions"

    def test_non_verbal_iq_partitions(self):
        data = {
            "datasetId": "SSC",
            "measure": "ssc_core_descriptive.ssc_diagnosis_nonverbal_iq",
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
            'measure': u'ssc_core_descriptive.ssc_diagnosis_nonverbal_iq',
            'left': {
                'count': 0,
                'percent': 0.0
            }
        }
        self.assertIn('right', data)
        self.assertIn('left', data)
        self.assertIn('mid', data)

        print(data)

#         self.assertEquals(
#             u'ssc_core_descriptive.ssc_diagnosis_nonverbal_iq',
#             data['measure']
#         )

        self.assertEquals(
            2574,
            data['right']['count']
        )
        self.assertEquals(
            204,
            data['mid']['count']
        )
