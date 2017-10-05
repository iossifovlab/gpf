'''
Created on Mar 30, 2017

@author: lubo
'''
from rest_framework.test import APITestCase
from rest_framework import status


class Test(APITestCase):

    URL = "/api/v3/measures/type/{}?datasetId=SSC"

    def test_measures_continuous(self):
        url = self.URL.format('continuous')
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.data

        self.assertEquals(1495, len(data))

    def test_measures_categorical(self):
        url = self.URL.format('categorical')
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.data
        self.assertEquals(3503, len(data))

        last = data[-1]

        self.assertEquals(
            last['measure'],
            'ssc_treatment_hx_school_classroom.age15_class_other_1on1_spec'
        )
        self.assertEquals(
            last['domain'],
            [u'0.0', u'100.0'])
