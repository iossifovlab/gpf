'''
Created on Jan 20, 2017

@author: lubo
'''
from rest_framework.test import APITestCase
from rest_framework import status
from users.management.commands import reload_datasets_perm


class DatasetApiTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        reload_datasets_perm.Command().handle()

    def test_get_datasets(self):
        url = '/api/v3/datasets/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertIn('data', data)
        self.assertEquals(3, len(data['data']))

    def test_get_dataset_ssc(self):
        url = '/api/v3/datasets/SSC'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertIn('data', data)
        print(data)
        data = data['data']
        self.assertIsNone(data['studyTypes'])

        self.assertIn('genotypeBrowser', data)
        gbdata = data['genotypeBrowser']
        self.assertFalse(gbdata['hasStudyTypes'])

    def test_get_dataset_sd(self):
        url = '/api/v3/datasets/SD'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertIn('data', data)
        pprint(data)
        data = data['data']
        self.assertEquals(['WE', 'TG'], data['studyTypes'])
        self.assertIn('genotypeBrowser', data)
        gbdata = data['genotypeBrowser']
        self.assertIn('hasStudyTypes', gbdata)
        pprint(gbdata)
        self.assertIn('phenoColumns', gbdata)

    def test_get_dataset_not_found(self):
        url = '/api/v3/datasets/ALA_BALA'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.data

        self.assertIn('error', data)
        pprint(data)

    def test_get_dataset_vip(self):
        url = '/api/v3/datasets/VIP'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertIn('data', data)
        pprint(data)
        data = data['data']
        self.assertIn('genotypeBrowser', data)
        gbdata = data['genotypeBrowser']
        self.assertFalse(gbdata['hasStudyTypes'])

        self.assertTrue(data['pedigreeSelectors'])
        pedigrees = data['pedigreeSelectors']
        self.assertEquals(2, len(pedigrees))

        pprint(gbdata)
        self.assertIn('phenoColumns', gbdata)
