'''
Created on Apr 5, 2016

@author: lubo
'''
from rest_framework import status
from users_api.tests.base_tests import BaseAuthenticatedUserTest
import pytest


@pytest.mark.skip(reason="no way of currently testing this")
class Tests(BaseAuthenticatedUserTest):

    def test_sentry_ssc_download_exception_request(self):
        data = {
            'denovoStudies': 'ALL SSC',
            'effectTypes': 'Missense',
            'families': 'Advanced',
            'familyIds': '',
            'familyPhenoMeasure': '',
            'familyPhenoMeasureMax': '',
            'familyPhenoMeasureMin': '',
            'familyPrbGender': 'All',
            'familyQuadTrio': 'Quad',
            'familyRace': 'white',
            'familySibGender': 'All',
            'familyVerbalIqHi': '',
            'familyVerbalIqLo': '',
            'gender': 'female,male',
            'gene_set_phenotype': 'autism',
            'geneRegion': '',
            'genes': 'Gene Sets',
            'geneSet': 'denovo',
            'geneSyms': '',
            'geneTerm': 'LGDs.Recurrent',
            'geneTermFilter': '',
            'geneWeight': '',
            'geneWeightMax': '',
            'geneWeightMin': '',
            'popFrequencyMax': '',
            'popFrequencyMin': '',
            'presentInChild': 'autism and unaffected,autism only',
            'presentInParent': 'mother only,father only,mother and father',
            'rarity': 'ultraRare',
            'variantTypes': 'CNV,del,ins,sub',
        }
        url = '/api/ssc_query_variants'
        response = self.client.post(url, data, format='json')
        self.assertEquals(status.HTTP_200_OK, response.status_code)

        response = self.client.post(
            url, data)
        self.assertEquals(status.HTTP_200_OK, response.status_code)

    def test_gene_list_exception(self):
        url = '/api/gene_set_list2?' \
            'desc=true&filter=&gene_set=main&key=true&page_count=200'
        response = self.client.get(url)
        self.assertEquals(status.HTTP_200_OK, response.status_code)

    def test_sentry_agre_with_rarity(self):
        data = {
            'denovoStudies': None,
            'effectTypes': 'LGDs',
            'families': 'All',
            'familyIds': '',
            'familyPrbGender': '',
            'familyQuadTrio': '',
            'familyRace': '',
            'familySibGender': '',
            'familyVerbalIqHi': '',
            'familyVerbalIqLo': '',
            'gene_set_phenotype': 'autism',
            'genes': 'All',
            'geneSet': '',
            'geneSyms': '',
            'geneTerm': '',
            'geneTermFilter': '',
            'geneWeight': '',
            'geneWeightMax': '',
            'geneWeightMin': '',
            'inChild': 'All',
            'max': '1.0',
            'min': '1.0',
            'popFrequencyMax': '',
            'popFrequencyMin': '',
            'rarity': 'ultraRare',
            'transmittedStudies': 'AGRE433',
            'variantTypes': 'All',
        }
        url = '/api/query_variants'
#         response = self.client.post(url, data, format='json')
#         self.assertEquals(status.HTTP_200_OK, response.status_code)

        response = self.client.post(url, data)
        self.assertEquals(status.HTTP_200_OK, response.status_code)
