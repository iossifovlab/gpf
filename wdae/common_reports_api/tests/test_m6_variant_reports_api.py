'''
Created on Aug 3, 2015

@author: lubo
'''
from rest_framework import status
from precompute import register
from common_reports_api.serializers import StudyVariantReportsSerializer
from users_api.tests.base_tests import BaseAuthenticatedUserTest
from tests.pytest_marks import slow


@slow
class Test(BaseAuthenticatedUserTest):

    def test_get_ok(self):
        url = '/api/v3/common_reports/variant_reports/IossifovWE2014'
        response = self.client.get(url, format='json')
        self.assertEquals(status.HTTP_200_OK, response.status_code)

    def test_get_not_found(self):
        url = '/api/v3/common_reports/variant_reports/AlaBalaPortokala'
        response = self.client.get(url, format='json')
        self.assertEquals(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_study_variant_report_serializer(self):
        variant_reports = register.get('variant_reports')
        self.assertIsNotNone(variant_reports)

        sr = variant_reports['IossifovWE2014']
        self.assertIsNotNone(sr)

        serializer = StudyVariantReportsSerializer(sr)
        self.assertTrue(serializer.data)

    def test_study_variant_report_iossifov2014(self):
        url = '/api/v3/common_reports/variant_reports/IossifovWE2014'
        response = self.client.get(url, format='json')
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertTrue(response.data)
        data = response.data
        self.assertIn('study_name', data)
        self.assertIn('study_description', data)
        self.assertIn('families_report', data)
        self.assertIn('denovo_report', data)

    def test_study_variant_report_iossifov2014_families_report(self):
        url = '/api/v3/common_reports/variant_reports/IossifovWE2014'
        response = self.client.get(url, format='json')
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertTrue(response.data)
        data = response.data['families_report']
        self.assertTrue(data)
        self.assertIn('phenotypes', data)
        self.assertIn('children_counters', data)
        self.assertIn('families_counters', data)
        self.assertIn('families_total', data)

    def test_study_variant_report_iossifov2014_denovo_report(self):
        url = '/api/v3/common_reports/variant_reports/IossifovWE2014'
        response = self.client.get(url, format='json')
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertTrue(response.data)
        data = response.data['denovo_report']
        self.assertTrue(data)
        self.assertIn('phenotypes', data)
        self.assertIn('effect_groups', data)
        self.assertIn('effect_types', data)
        self.assertIn('rows', data)

    def test_study_variant_report_iossifov2014_denovo_report_rows(self):
        url = '/api/v3/common_reports/variant_reports/IossifovWE2014'
        response = self.client.get(url, format='json')
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertTrue(response.data)
        data = response.data['denovo_report']['rows']
        self.assertTrue(data)
        self.assertEqual('LGDs', data[0]['effect_type'])
        autism = data[0]['row'][0]
        value = autism['events_count']
        # FIXME: changed after rennotation
        # self.assertEquals(383, value)
        self.assertEquals(388, value)
        value = autism['events_children_count']
        # self.assertEquals(357, value)
        self.assertEquals(362, value)
        value = autism['events_rate_per_child']
        self.assertAlmostEqual(0.155, value, 3)
        value = autism['events_children_percent']
        self.assertAlmostEqual(0.144, value, 3)
