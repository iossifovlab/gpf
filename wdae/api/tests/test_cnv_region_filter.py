'''
Created on Jan 4, 2016

@author: lubo
'''
from rest_framework import status
from users_api.tests.base_tests import BaseAuthenticatedUserTest
import pytest


@pytest.mark.skip(reason="no way of currently testing this")
class Test(BaseAuthenticatedUserTest):

    def test_cnv_region(self):
        data = {
            'geneRegion': '1:240530000-242300000',
            "effectTypes": "CNV+",
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "None",
            "presentInChild": "autism only",
            "gender": "male,female",
        }

        url = '/api/ssc_query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('2', response.data['count'])

    def test_all_region(self):
        data = {
            'geneRegion': '1:240530000-242300000',
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "None",
            "presentInChild": "autism only",
            "gender": "male,female",
        }

        url = '/api/ssc_query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('4', response.data['count'])

    def test_all_effects_region_and_gene(self):
        data = {
            "geneSyms": "WDR64",
            'geneRegion': '1:240530000-242300000',
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "None",
            "presentInChild": "autism only",
            "gender": "male,female",
        }

        url = '/api/ssc_query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('2', response.data['count'])
