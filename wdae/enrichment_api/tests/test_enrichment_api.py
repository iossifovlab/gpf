'''
Created on Feb 17, 2017

@author: lubo
'''


from rest_framework import status
from rest_framework.test import APITestCase


class Test(APITestCase):

    def test_bad_genes(self):
        data = {
        }
        url = '/api/v3/enrichment/test/SD'

        response = self.client.post(url, data)
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)
