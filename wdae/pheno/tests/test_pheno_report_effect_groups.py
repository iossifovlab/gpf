'''
Created on Apr 28, 2016

@author: lubo
'''
import unittest
from pheno.report import family_pheno_query_variants
from rest_framework.test import APITestCase


class Test(unittest.TestCase):

    def test_single_gene_sym_lgds_only(self):
        data = {
            'denovoStudies': 'ALL SSC',
            'transmittedStudies': 'w1202s766e611',
            'presentInParent': "father only",
            'geneSyms': "POGZ",

        }
        res = family_pheno_query_variants(data, ['LGDs'])

        self.assertIn('LGDs', res)
        self.assertNotIn('missense', res)
        self.assertNotIn('synonymous', res)
        self.assertNotIn('CNV+,CNV-', res)
        self.assertEqual(1, len(res.keys()))
        self.assertEqual(0, len(res['LGDs']))
#         self.assertEqual(42, len(res['missense']))
#         self.assertEqual(119, len(res['synonymous']))
#         self.assertEqual(0, len(res['CNV+,CNV-']))

    def test_single_gene_sym_lgds_and_missense(self):
        data = {
            'denovoStudies': 'ALL SSC',
            'transmittedStudies': 'w1202s766e611',
            'presentInParent': "father only",
            'geneSyms': "POGZ",

        }
        res = family_pheno_query_variants(data, ['LGDs', 'missense'])

        self.assertIn('LGDs', res)
        self.assertIn('missense', res)
        self.assertNotIn('synonymous', res)
        self.assertNotIn('CNV+,CNV-', res)
        self.assertEqual(2, len(res.keys()))
        self.assertEqual(0, len(res['LGDs']))
        self.assertEqual(42, len(res['missense']))
#         self.assertEqual(119, len(res['synonymous']))
#         self.assertEqual(0, len(res['CNV+,CNV-']))


class TestViews(APITestCase):

    def test_single_gene_sym_lgds_only(self):
        url = "/api/v2/pheno_reports"
        data = {
            'denovoStudies': 'ALL SSC',
            'transmittedStudies': 'w1202s766e611',
            'presentInParent': "father only",
            'geneSyms': "POGZ",
            'phenoMeasure': 'head_circumference',
            'effectTypeGroups': 'LGDs'

        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        data = response.data['data']
        self.assertEquals(2, len(data))
        self.assertEquals('LGDs', data[0][0])
        self.assertEquals('LGDs', data[1][0])

    def test_single_gene_sym_lgds_and_missense(self):
        url = "/api/v2/pheno_reports"
        data = {
            'denovoStudies': 'ALL SSC',
            'transmittedStudies': 'w1202s766e611',
            'presentInParent': "father only",
            'geneSyms': "POGZ",
            'phenoMeasure': 'head_circumference',
            'effectTypeGroups': 'LGDs,missense'

        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        data = response.data['data']
        self.assertEquals(4, len(data))
        self.assertEquals('LGDs', data[0][0])
        self.assertEquals('LGDs', data[1][0])
        self.assertEquals('missense', data[2][0])
        self.assertEquals('missense', data[3][0])
