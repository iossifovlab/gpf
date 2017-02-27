'''
Created on Feb 17, 2017

@author: lubo
'''


from rest_framework import status
from rest_framework.test import APITestCase
from pprint import pprint


class Test(APITestCase):

    def test_bad_request(self):
        data = {
            'enrichmentBackgroundModel': 'synonymousBackgroundModel',
            'enrichmentCountingModel': 'enrichmentGeneCounting',
        }
        url = '/api/v3/enrichment/test/SD'

        response = self.client.post(url, data, format='json')
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_gene_set_denovo_lgds_rec_sd(self):
        data = {
            'enrichmentBackgroundModel': 'synonymousBackgroundModel',
            'enrichmentCountingModel': 'enrichmentGeneCounting',
            'geneSet': {
                'geneSetsCollection': 'denovo',
                'geneSet': 'LGDs.Recurrent',
                'geneSetsTypes': ['autism'],
            }
        }
        url = '/api/v3/enrichment/test/SD'

        response = self.client.post(url, data, format='json')
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        pprint(response.data)
        data = response.data

        self.assertEquals(546, data['autism']['LGDs']['all']['count'])
        self.assertEquals(45, data['autism']['LGDs']['rec']['count'])

    def test_gene_set_denovo_main_autism_candidates_sd(self):
        data = {
            'enrichmentBackgroundModel': 'synonymousBackgroundModel',
            'enrichmentCountingModel': 'enrichmentGeneCounting',
            'geneSet': {
                'geneSetsCollection': 'main',
                'geneSet': 'autism candidates from Iossifov PNAS 2015',
            }
        }
        url = '/api/v3/enrichment/test/SD'

        response = self.client.post(url, data, format='json')
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        pprint(response.data)
        data = response.data

        self.assertEquals(546, data['autism']['LGDs']['all']['count'])
        self.assertEquals(45, data['autism']['LGDs']['rec']['count'])

        self.assertEquals(222, data['unaffected']['LGDs']['all']['count'])

    def test_gene_set_denovo_lgds_rec_ssc(self):
        data = {
            'enrichmentBackgroundModel': 'synonymousBackgroundModel',
            'enrichmentCountingModel': 'enrichmentGeneCounting',
            'geneSet': {
                'geneSetsCollection': 'denovo',
                'geneSet': 'LGDs.Recurrent',
                'geneSetsTypes': ['autism'],
            }
        }
        url = '/api/v3/enrichment/test/SSC'

        response = self.client.post(url, data, format='json')
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        pprint(response.data)
        data = response.data

        self.assertEquals(388, data['autism']['LGDs']['all']['count'])
        self.assertEquals(28, data['autism']['LGDs']['rec']['count'])
