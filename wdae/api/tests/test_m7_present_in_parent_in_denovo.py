'''
Created on Oct 23, 2015

@author: lubo
'''
from rest_framework import status
from users_api.tests.base_tests import BaseAuthenticatedUserTest
import pytest


@pytest.mark.skip(reason="no way of currently testing this")
class Test(BaseAuthenticatedUserTest):

    def testName(self):
        url = "/api/ssc_query_variants_preview"
        request = {
            'gene_set_phenotype': 'autism',
            'denovoStudies': 'ALL SSC',
            'families': 'familyIds',
            'familyIds': '11110',
            'gender': 'female,male',
            'genes': 'All',
            'rarity': 'all',
            'effectTypes':
            "frame-shift,intergenic,intron,missense,non-coding,"
            "no-frame-shift,nonsense,splice-site,synonymous,noEnd,"
            "noStart,3'UTR,5'UTR,CNV+,CNV-,3'UTR,3'UTR-intron,5'UTR,"
            "5'UTR-intron",
            'presentInChild': 'autism only',
            'variantTypes': 'CNV,del,ins,sub',
            'presentInParent': 'father only,mother and father,mother only,'
            'neither',
            'transmittedStudies': 'w1202s766e611'
        }

        response = self.client.post(url, request, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_no_denovo(self):
        url = "/api/ssc_query_variants_preview"
        request = {
            'families': 'All',
            'denovoStudies': 'ALL SSC',
            'gender': 'female,male',
            'genes': 'Gene Sets',
            'rarity': 'ultraRare',
            'effectTypes': 'frame-shift,nonsense,splice-site',
            'presentInChild': 'autism and unaffected,autism only',
            'variantTypes': 'CNV,del,ins,sub',
            'presentInParent': 'father only,mother and father,mother only',
            'transmittedStudies': 'w1202s766e611',
            'limit': 2000,
            'geneTerm': 'LGDs',
            'geneSet': 'denovo',
            'gene_set_phenotype': 'intellectual disability',
        }

        response = self.client.post(url, request, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEquals('12', response.data['count'])

    def test_has_denovo(self):
        url = "/api/ssc_query_variants_preview"
        request = {
            'families': 'All',
            'denovoStudies': 'ALL SSC',
            'gender': 'female,male',
            'genes': 'Gene Sets',
            'rarity': 'ultraRare',
            'effectTypes': 'frame-shift,nonsense,splice-site',
            'presentInChild': 'autism and unaffected,autism only',
            'variantTypes': 'CNV,del,ins,sub',
            'presentInParent':
            'father only,mother and father,mother only,neither',
            'transmittedStudies': 'w1202s766e611',
            'limit': 2000,
            'geneTerm': 'LGDs',
            'geneSet': 'denovo',
            'gene_set_phenotype': 'intellectual disability',
        }

        response = self.client.post(url, request, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEquals('24', response.data['count'])
