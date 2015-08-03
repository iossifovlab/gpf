'''
Created on Aug 3, 2015

@author: lubo
'''
import unittest
from rest_framework import status
from rest_framework.test import APITestCase
from api.precompute import register
from api.reports.serializers import StudyVariantReportsSerializer


class Test(APITestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_ok(self):
        url = '/api/reports/variant_reports/IossifovWE2014'
        response = self.client.get(url, format='json')
        self.assertEquals(status.HTTP_200_OK, response.status_code)

    def test_get_not_found(self):
        url = '/api/reports/variant_reports/AlaBalaPortokala'
        response = self.client.get(url, format='json')
        self.assertEquals(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_study_variant_report_serializer(self):
        variant_reports = register.get('variant_reports')
        self.assertIsNotNone(variant_reports)

        sr = variant_reports['IossifovWE2014']
        self.assertIsNotNone(sr)

        serializer = StudyVariantReportsSerializer(sr)
        self.assertTrue(serializer.data)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
