'''
Created on Dec 10, 2015

@author: lubo
'''
import unittest
from rest_framework.test import APITestCase


class Test(APITestCase):

    def test_preview_view(self):
        url = "/api/v2/gene_weights"
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        print(response.data)

if __name__ == "__main__":
    unittest.main()
