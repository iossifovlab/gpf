'''
Created on Jan 20, 2017

@author: lubo
'''
from rest_framework import status
from users_api.tests.base_tests import BaseAuthenticatedUserTest


class DatasetApiTest(BaseAuthenticatedUserTest):

    def test_get_dataset_ssc(self):
        url = '/api/v3/datasets/SSC'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertIn('data', data)
        data = data['data']
        self.assertIn('accessRights', data)
        self.assertTrue(data['accessRights'])

    def test_get_dataset_sd(self):
        url = '/api/v3/datasets/SD_TEST'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertIn('data', data)

        data = data['data']
        self.assertIn('accessRights', data)
        self.assertTrue(data['accessRights'])

    def test_get_dataset_svip(self):
        url = '/api/v3/datasets/SVIP'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertIn('data', data)
        data = data['data']
        self.assertIn('accessRights', data)
        self.assertTrue(data['accessRights'])
