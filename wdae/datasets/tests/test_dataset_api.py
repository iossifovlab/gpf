'''
Created on Jan 20, 2017

@author: lubo
'''
from rest_framework.test import APITestCase
from rest_framework import status


class DatasetApiTest(APITestCase):

    def test_get_datasets(self):
        url = '/api/v3/dataset'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertIn('data', data)
        self.assertEquals(3, len(data['data']))

    def test_get_dataset_ssc(self):
        url = '/api/v3/dataset/SSC'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertIn('data', data)
        print(data)

    def test_get_dataset_sd(self):
        url = '/api/v3/dataset/SD'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertIn('data', data)
        print(data)

    def test_get_dataset_not_found(self):
        url = '/api/v3/dataset/ALA_BALA'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.data

        self.assertIn('error', data)
        print(data)
