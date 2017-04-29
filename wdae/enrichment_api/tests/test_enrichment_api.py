'''
Created on Feb 17, 2017

@author: lubo
'''


from rest_framework import status
from rest_framework.test import APITestCase


class Test(APITestCase):

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
            'datasetId': 'SD',
            'enrichmentBackgroundModel': 'synonymousBackgroundModel',
            'enrichmentCountingModel': 'enrichmentGeneCounting',
            'geneSet': {
                'geneSetsCollection': 'denovo',
                'geneSet': 'LGDs.Recurrent',
                'geneSetsTypes': ['autism'],
            }
        }
        url = '/api/v3/enrichment/test'

        response = self.client.post(url, data, format='json')
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        data = response.data

        self.assertEquals(546, data['result'][0]['LGDs']['all']['count'])
        self.assertEquals(39, data['result'][0]['LGDs']['rec']['count'])

    def test_gene_set_denovo_main_autism_candidates_sd(self):
        data = {
            'datasetId': 'SD',
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

        self.assertEquals(546, data['result'][0]['LGDs']['all']['count'])
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
                'geneSetsTypes': ['autism'],
            }
        }
        url = '/api/v3/enrichment/test'

        response = self.client.post(url, data, format='json')
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        data = response.data

        self.assertEquals(386, data['result'][0]['LGDs']['all']['count'])
        self.assertEquals(28, data['result'][0]['LGDs']['rec']['count'])
