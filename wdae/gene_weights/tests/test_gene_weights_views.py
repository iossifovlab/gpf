'''
Created on Dec 10, 2015

@author: lubo
'''
import unittest
from rest_framework.test import APITestCase


class GeneWeightsListViewTest(APITestCase):

    def test_gene_weights_list_view(self):
        url = "/api/v2/gene_weights"
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        print(response.data)
        self.assertEqual(3, len(response.data))
        for w in response.data:
            self.assertIn('min', w)
            self.assertIn('max', w)
            self.assertIn('desc', w)
            self.assertIn('weight', w)


if __name__ == "__main__":
    unittest.main()
