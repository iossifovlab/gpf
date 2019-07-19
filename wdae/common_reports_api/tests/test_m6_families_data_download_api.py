'''
Created on Aug 3, 2015

@author: lubo
'''
import unittest
from rest_framework import status
from users_api.tests.base_tests import BaseAuthenticatedUserTest
from tests.pytest_marks import slow


@slow
class Test(BaseAuthenticatedUserTest):

    def test_get_ok(self):
        url = '/api/v3/common_reports/families_data/IossifovWE2014'
        response = self.client.get(url)
        self.assertEquals(status.HTTP_200_OK, response.status_code)

    def test_get_not_found(self):
        url = '/api/v3/common_reports/families_data/AlaBalaPortokala'
        response = self.client.get(url)
        self.assertEquals(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_get_content(self):
        url = '/api/v3/common_reports/families_data/IossifovWE2014'
        response = self.client.get(url)
        self.assertEquals(status.HTTP_200_OK, response.status_code)

        for num, _line in enumerate(response.streaming_content):
            pass
        self.assertEqual(9448 + 1, num)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
