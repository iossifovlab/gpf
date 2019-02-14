'''
Created on May 27, 2017

@author: lubo
'''
from users_api.tests.base_tests import BaseAuthenticatedUserTest
from rest_framework import status
from pprint import pprint


class Test(BaseAuthenticatedUserTest):

    URL = '/api/v3/common_reports/variant_reports/IossifovWE2014'
    URL2 = '/api/v3/common_reports/variant_reports/TEST%20WHOLE%20EXOME'

    def test_has_study_description(self):
        response = self.client.get(self.URL)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        data = response.data
        self.assertIn('study_description', data)

    def test_has_study_description2(self):
        response = self.client.get(self.URL2)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        data = response.data
        self.assertIn('study_description', data)
        self.assertEqual(
            data['study_description'],
            "Test whole-exomes studies")

    def test_denovo_children_counters(self):
        response = self.client.get(self.URL)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.data['denovo_report']
        pprint(data.keys())

    def test_denovo_children_counters2(self):
        response = self.client.get(self.URL2)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.data['denovo_report']
        pprint(data.keys())

        self.assertEquals(
            data['phenotypes'],
            [
                'autism',
                'congenital heart disease',
                'epilepsy',
                'intellectual disability',
                'schizophrenia',
                'unaffected'
            ]
        )
        self.assertEquals(
            data['effect_groups'],
            [
                'LGDs', 'nonsynonymous', 'UTRs'
            ]
        )
        self.assertEquals(
            data['effect_types'],
            [
                'Nonsense',
                'Frame-shift',
                'Splice-site',
                'Missense',
                'No-frame-shift',
                'noStart',
                'noEnd',
                'Synonymous',
                'Non coding',
                'Intron',
                'Intergenic',
                "3'-UTR",
                "5'-UTR"
            ])
