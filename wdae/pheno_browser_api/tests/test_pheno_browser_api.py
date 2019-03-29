'''
Created on Apr 21, 2017

@author: lubo
'''
import pytest

from rest_framework import status
from rest_framework.test import APITestCase


class Test(APITestCase):

    URL = "/api/v3/pheno_browser/instruments"
    MEASURES_URL = "/api/v3/pheno_browser/measures"
    DOWNLOAD_URL = "/api/v3/pheno_browser/download"

    def test_instruments_missing_dataset_id(self):
        response = self.client.get(self.URL)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    @pytest.mark.skip('missing ssc dataset')
    def test_instruments_ssc(self):
        url = "{}?dataset_id=SSC".format(self.URL)
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertIn('default', response.data)
        self.assertIn('instruments', response.data)
        self.assertEqual(103, len(response.data['instruments']))

    @pytest.mark.skip('missing ssc dataset')
    def test_measures_ssc_commonly_used(self):
        url = "{}?dataset_id=SSC&instrument=ssc_commonly_used".format(
            self.MEASURES_URL)
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertIn('base_image_url', response.data)
        self.assertIn('measures', response.data)

    def test_instruments_svip(self):
        url = "{}?dataset_id=SVIP".format(self.URL)
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertIn('default', response.data)
        self.assertIn('instruments', response.data)
        self.assertEqual(71, len(response.data['instruments']))

    def test_measures_svip_diagnosis_summary(self):
        url = "{}?dataset_id=SVIP&instrument=diagnosis_summary".format(
            self.MEASURES_URL)
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertIn('base_image_url', response.data)
        self.assertIn('measures', response.data)

        self.assertEqual(169, len(response.data['measures']))

    def test_measures_svip_bad_json(self):
        problem_urls = [
            "{}?dataset_id=SVIP&instrument=svip_neuro_exam",
            "{}?dataset_id=SVIP&instrument=svip_subjects",
        ]
        urls = [u.format(self.MEASURES_URL)for u in problem_urls]

        for url in urls:
            response = self.client.get(url)
            self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_download_svip_diagnosis_summary(self):
        url = "{}?dataset_id=SVIP&instrument=diagnosis_summary".format(
            self.DOWNLOAD_URL)
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        header = response.content.decode("utf-8").split()[0].split(',')
        self.assertEqual(header[0], 'person_id')
