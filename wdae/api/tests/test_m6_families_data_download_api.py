'''
Created on Aug 3, 2015

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

    def test_get_ok(self):
        url = '/api/reports/families_data/IossifovWE2014'
        response = self.client.get(url)
        self.assertEquals(status.HTTP_200_OK, response.status_code)

    def test_get_not_found(self):
        url = '/api/reports/families_data/AlaBalaPortokala'
        response = self.client.get(url)
        self.assertEquals(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_get_content(self):
        url = '/api/reports/families_data/IossifovWE2014'
        response = self.client.get(url)
        self.assertEquals(status.HTTP_200_OK, response.status_code)

        for num, _line in enumerate(response.streaming_content):
            pass
        self.assertEqual(9452 + 1, num)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
