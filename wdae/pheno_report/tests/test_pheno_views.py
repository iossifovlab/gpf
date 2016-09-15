'''
Created on Nov 16, 2015

@author: lubo
'''
import unittest
from rest_framework.test import APITestCase


def count_iterable(iterable):
    for num, _it in enumerate(iterable):
        pass
    return num + 1


class Test(APITestCase):

    def test_preview_view(self):
        url = "/api/v2/pheno_reports"
        data = {
            'denovoStudies': 'ala bala',
            'phenoMeasure': 'ssc_commonly_used.head_circumference',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        self.assertIn('measure', response.data)
        self.assertEqual(
            'ssc_commonly_used.head_circumference', response.data['measure'])
        self.assertEqual(
            'ssc_commonly_used.head_circumference', response.data['formula'])

    def test_report_normalized_by_age(self):
        url = "/api/v2/pheno_reports"
        data = {
            'denovoStudies': 'ala bala',
            'phenoMeasure': 'ssc_commonly_used.head_circumference',
            'normalizedBy': 'normByAge',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        self.assertIn('measure', response.data)
        self.assertEqual(
            'ssc_commonly_used.head_circumference', response.data['measure'])
        self.assertEqual(
            'ssc_commonly_used.head_circumference ~ pheno_common.age',
            response.data['formula'])

    def test_report_without_normalized_by_age(self):
        url = "/api/v2/pheno_reports"
        data = {
            'denovoStudies': 'ala bala',
            'phenoMeasure': 'ssc_commonly_used.head_circumference',
            'normalizedBy': "",
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        self.assertIn('measure', response.data)
        self.assertEqual(
            'ssc_commonly_used.head_circumference', response.data['measure'])
        self.assertEqual(
            'ssc_commonly_used.head_circumference', response.data['formula'])

    def test_report_nviq_normalized_by_nviq(self):
        url = "/api/v2/pheno_reports"
        data = {
            u'phenoMeasure': u'pheno_common.non_verbal_iq',
            u'denovoStudies': u'ALL SSC',
            u'families': u'All',
            u'gene_set_phenotype': u'autism',
            u'normalizedBy': u'normByNVIQ',
            u'genes': u'All',
            u'effectTypeGroups': u'LGDs,Missense,Synonymous,CNV',
            u'presentInParent': u'neither'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)

    def test_download_view(self):
        url = "/api/v2/pheno_reports/download"
        data = {
            'denovoStudies': 'ala bala',
            'phenoMeasure': 'ssc_commonly_used.head_circumference',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        data = response.streaming_content
        self.assertIsNotNone(data)
        self.assertEquals(2729, count_iterable(data))


class PhenoMeasuresTest(APITestCase):

    def test_get_pheno_measures(self):
        url = "/api/v2/pheno_reports/measures"
        response = self.client.get(url, format='json')
        self.assertEqual(200, response.status_code)
        self.assertEqual(526, len(response.data))

if __name__ == "__main__":
    unittest.main()
