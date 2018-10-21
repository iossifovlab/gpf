'''
Created on Feb 17, 2017

@author: lubo
'''
from __future__ import print_function

from rest_framework import status
from users_api.tests.base_tests import BaseAuthenticatedUserTest
from tests.pytest_marks import slow


class Test(BaseAuthenticatedUserTest):

    @slow
    def test_gene_set_denovo_main_autism_candidates_denovo_db(self):
        data = {
            'datasetId': 'TESTdenovo_db',
            'enrichmentBackgroundModel': 'synonymousBackgroundModel',
            'enrichmentCountingModel': 'enrichmentGeneCounting',
            'geneSet': {
                'geneSetsCollection': 'main',
                'geneSet': 'autism candidates from Iossifov PNAS 2015',
            }
        }
        url = '/api/v3/enrichment/test'

        response = self.client.post(url, data, format='json')
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        data = response.data

        assert data['result']

        res = data['result'][0]
        self.assertEquals(0, res['LGDs']['all']['count'])
        self.assertEquals(0, res['LGDs']['rec']['count'])

        res = data['result'][3]
        self.assertEquals('autism', res['selector'])
        self.assertEquals(78, res['LGDs']['all']['count'])
        self.assertEquals(8, res['LGDs']['rec']['count'])

        res = data['result'][-1]
        self.assertEquals('unaffected', res['selector'])
        self.assertEquals(19, res['LGDs']['all']['count'])

    def test_bad_request(self):
        data = {
            'enrichmentBackgroundModel': 'synonymousBackgroundModel',
            'enrichmentCountingModel': 'enrichmentGeneCounting',
        }
        url = '/api/v3/enrichment/test'

        response = self.client.post(url, data, format='json')
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_gene_set_denovo_lgds_rec_sd(self):
        data = {
            'datasetId': 'SD_TEST',
            'enrichmentBackgroundModel': 'synonymousBackgroundModel',
            'enrichmentCountingModel': 'enrichmentGeneCounting',
            'geneSet': {
                'geneSetsCollection': 'denovo',
                'geneSet': 'LGDs.Recurrent',
                'geneSetsTypes': {
                    'SD_TEST': ['autism']
                }
            }
        }
        url = '/api/v3/enrichment/test'

        response = self.client.post(url, data, format='json')
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        data = response.data

        # self.assertEquals(546, data['result'][0]['LGDs']['all']['count'])
        self.assertEquals(551, data['result'][0]['LGDs']['all']['count'])
        self.assertEquals(39, data['result'][0]['LGDs']['rec']['count'])

    def test_gene_set_denovo_main_autism_candidates_sd(self):
        data = {
            'datasetId': 'SD_TEST',
            'enrichmentBackgroundModel': 'synonymousBackgroundModel',
            'enrichmentCountingModel': 'enrichmentGeneCounting',
            'geneSet': {
                'geneSetsCollection': 'main',
                'geneSet': 'autism candidates from Iossifov PNAS 2015',
            }
        }
        url = '/api/v3/enrichment/test'

        response = self.client.post(url, data, format='json')
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        data = response.data

        # self.assertEquals(546, data['result'][0]['LGDs']['all']['count'])
        self.assertEquals(551, data['result'][0]['LGDs']['all']['count'])
        self.assertEquals(39, data['result'][0]['LGDs']['rec']['count'])

        self.assertEquals('unaffected', data['result'][5]['selector'])
        self.assertEquals(220, data['result'][5]['LGDs']['all']['count'])

    def test_gene_set_denovo_lgds_rec_ssc(self):
        data = {
            'datasetId': 'SSC',
            'enrichmentBackgroundModel': 'synonymousBackgroundModel',
            'enrichmentCountingModel': 'enrichmentGeneCounting',
            'geneSet': {
                'geneSetsCollection': 'denovo',
                'geneSet': 'LGDs.Recurrent',
                'geneSetsTypes': {
                    'SD_TEST': ['autism']
                }
            }
        }
        url = '/api/v3/enrichment/test'

        response = self.client.post(url, data, format='json')
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        data = response.data

        # self.assertEquals(386, data['result'][0]['LGDs']['all']['count'])
        self.assertEquals(391, data['result'][0]['LGDs']['all']['count'])
        self.assertEquals(28, data['result'][0]['LGDs']['rec']['count'])
        self.assertEquals(
            "Gene Set: LGDs.Recurrent (SD_TEST:autism) (44)", data['desc'])

    def test_gene_syms_description(self):
        data = {
            'datasetId': 'SSC',
            'enrichmentBackgroundModel': 'synonymousBackgroundModel',
            'enrichmentCountingModel': 'enrichmentGeneCounting',
            "geneSymbols": [
                "POGZ"
            ]
        }
        url = '/api/v3/enrichment/test'

        response = self.client.post(url, data, format='json')
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        data = response.data

        self.assertEquals(
            "Gene Symbols: POGZ (1)", data['desc'])
