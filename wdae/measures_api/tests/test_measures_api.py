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
        print(url)
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.data

        self.assertEquals(526, len(data))

        last = data[-1]
        print(last)

        self.assertEquals(last['measure'], 'pheno_common.verbal_iq')
        self.assertEquals(last['max'], 167.0)
        self.assertEquals(last['min'], 5)

    def test_measures_categorical(self):
        url = self.URL.format('categorical')
        print(url)
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.data
        self.assertEquals(1025, len(data))

        last = data[-1]
        print(last)

        self.assertEquals(last['measure'], 'pheno_common.race')
        self.assertEquals(
            last['domain'],
            [u'white', u'asian', u'other', u'more-than-one-race',
             u'african-amer', u'not-specified', u'native-american',
             u'native-hawaiian'])
