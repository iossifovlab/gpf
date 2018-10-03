'''
Created on Jan 20, 2017

@author: lubo
'''
from __future__ import print_function
from builtins import next
from rest_framework.test import APITestCase
from rest_framework import status
from guardian.shortcuts import get_groups_with_perms
from datasets_api.models import Dataset


class DatasetApiTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        Dataset.recreate_dataset_perm('SD', [])
        Dataset.recreate_dataset_perm('SD_TEST', [])
        Dataset.recreate_dataset_perm('SSC', [])
        Dataset.recreate_dataset_perm('SVIP', [])
        Dataset.recreate_dataset_perm('TEST', [])
        Dataset.recreate_dataset_perm('SPARKv1', [])
        Dataset.recreate_dataset_perm('SPARKv2', [])
        Dataset.recreate_dataset_perm('AGRE_WG', [])
        Dataset.recreate_dataset_perm('SSC_WG', [])
        Dataset.recreate_dataset_perm('denovo_db', [])
        Dataset.recreate_dataset_perm('TESTdenovo_db', [])

    def test_get_datasets(self):
        url = '/api/v3/datasets'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertIn('data', data)
        # print(data)
        # self.assertEquals(8, len(data['data']))

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

        phenoFiltersName = [phenoFilter['name']
                            for phenoFilter in gbdata['phenoFilters']]
        self.assertIn("Mother Race", phenoFiltersName)
        self.assertIn("Father Race", phenoFiltersName)
        self.assertIn("Proband Pheno Measure", phenoFiltersName)

        familyStudyFilters = [phenoFilter['name']
                              for phenoFilter in gbdata['familyStudyFilters']]
        self.assertIn("Study", familyStudyFilters)
        self.assertIn("Study Type", familyStudyFilters)

    def test_get_dataset_sd(self):
        url = '/api/v3/datasets/SD_TEST'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertIn('data', data)
        data = data['data']
        self.assertEquals(['WE', 'TG'], data['studyTypes'])
        self.assertIn('genotypeBrowser', data)
        gbdata = data['genotypeBrowser']
        self.assertIn('hasStudyTypes', gbdata)
        self.assertIn('phenoColumns', gbdata)

    def test_get_dataset_not_found(self):
        url = '/api/v3/datasets/ALA_BALA'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.data

        self.assertIn('error', data)

    def test_get_dataset_svip(self):
        url = '/api/v3/datasets/SVIP'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertIn('data', data)
        data = data['data']
        self.assertIn('genotypeBrowser', data)
        gbdata = data['genotypeBrowser']
        self.assertFalse(gbdata['hasStudyTypes'])

        self.assertTrue(data['pedigreeSelectors'])
        pedigrees = data['pedigreeSelectors']
        self.assertEquals(2, len(pedigrees))

        self.assertIn('phenoColumns', gbdata)

    def test_datasets_have_default_groups(self):
        url = '/api/v3/datasets'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertIn('data', data)
        for dataset in data['data']:
            dataset_id = dataset['id']
            assert next((group for group in dataset['groups']
                         if group['name'] == dataset_id), None)

    def test_datasets_have_all_their_groups(self):
        url = '/api/v3/datasets'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertIn('data', data)
        for dataset_response in data['data']:
            dataset_id = dataset_response['id']
            dataset = Dataset.objects.get(dataset_id=dataset_id)
            dataset_groups = get_groups_with_perms(dataset)

            assert len(dataset_groups) == len(dataset_response['groups'])
            for group in dataset_groups:
                assert next((g for g in dataset_response['groups']
                             if g['name'] == group.name), None)
