'''
Created on Apr 21, 2017

@author: lubo
'''
import os

from datasets_api.studies_manager import StudiesManager
from configurable_entities.configuration import DAEConfig

from rest_framework import status
from rest_framework.test import APITestCase


class Test(APITestCase):

    URL = "/api/v3/pheno_browser/instruments"
    MEASURES_URL = "/api/v3/pheno_browser/measures"
    DOWNLOAD_URL = "/api/v3/pheno_browser/download"

    def setUp(self):
        # inject testing data fixtures
        init = StudiesManager.__init__

        fixtures_dir = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                'fixtures'))

        fake_dae_config = DAEConfig(fixtures_dir)

        def new_init(self, dae_config=None):
            init(self, fake_dae_config)

        StudiesManager.__init__ = new_init

    def test_instruments_missing_dataset_id(self):
        response = self.client.get(self.URL)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_instruments(self):
        url = "{}?dataset_id=quads_f1_ds".format(self.URL)
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertIn('default', response.data)
        self.assertIn('instruments', response.data)
        self.assertEqual(3, len(response.data['instruments']))

    def test_measures(self):
        url = "{}?dataset_id=quads_f1_ds&instrument=instrument1".format(
            self.MEASURES_URL)
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertIn('base_image_url', response.data)
        self.assertIn('measures', response.data)
        self.assertEqual(4, len(response.data['measures']))

    def test_download(self):
        url = "{}?dataset_id=quads_f1_ds&instrument=instrument1".format(
            self.DOWNLOAD_URL)
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        header = response.content.decode("utf-8").split()[0].split(',')
        self.assertEqual(header[0], 'person_id')
