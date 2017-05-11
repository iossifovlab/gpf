'''
Created on Apr 28, 2016

@author: lubo
'''
import unittest
from pheno_report import pheno_request, pheno_tool
from users_api.tests.base_tests import BaseAuthenticatedUserTest


class Test(unittest.TestCase):

    def test_single_gene_sym_lgds_only(self):
        data = {
            'denovoStudies': 'ALL SSC',
            'phenoMeasure': 'ssc_commonly_used.head_circumference',
            'transmittedStudies': 'w1202s766e611',
            'presentInParent': "father only",
            'geneSyms': "POGZ",
            'effectTypeGroups': 'LGDs',

        }
        req = pheno_request.Request(data)
        tool = pheno_tool.PhenoTool(req)

        res = tool.calc()

        self.assertEquals(2, len(res))
        [male, female] = res
        self.assertEquals(male['effectType'], 'LGDs')
        self.assertEquals(female['effectType'], 'LGDs')


class TestViews(BaseAuthenticatedUserTest):

    def test_single_gene_sym_lgds_only(self):
        url = "/api/v2/pheno_reports"
        data = {
            'denovoStudies': 'ALL SSC',
            'transmittedStudies': 'w1202s766e611',
            'presentInParent': "father only",
            'geneSyms': "POGZ",
            'phenoMeasure': 'ssc_commonly_used.head_circumference',
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
            'phenoMeasure': 'ssc_commonly_used.head_circumference',
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
