'''
Created on Oct 23, 2015

@author: lubo
'''
from rest_framework import status
from users_api.tests.base_tests import BaseAuthenticatedUserTest


class Test(BaseAuthenticatedUserTest):

    def test_verbal_iq_from0_to50(self):
        url = "/api/ssc_query_variants_preview"
        request = {
            'gene_set_phenotype': 'autism',
            'denovoStudies': 'ALL SSC',
            'families': 'familyIds',
            # 'familyIds': '11000,11110,12119,11071,11077,14673',
            'gender': 'female,male',
            'genes': 'All',
            'rarity': 'all',
            'effectTypes': "frame-shift",
            'presentInChild': 'autism only',
            'variantTypes': 'CNV,del,ins,sub',
            'presentInParent': 'neither',
            'transmittedStudies': 'w1202s766e611',
            'familyPhenoMeasure': "pheno_common.verbal_iq",
            'familyPhenoMeasureMin': 0,
            'familyPhenoMeasureMax': 50,
        }

        response = self.client.post(url, request, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('43', response.data['count'])

    def test_verbal_iq_from49_to50(self):
        url = "/api/ssc_query_variants_preview"
        request = {
            'gene_set_phenotype': 'autism',
            'denovoStudies': 'ALL SSC',
            'families': 'familyIds',
            # 'familyIds': '11000,11110,12119',
            'gender': 'female,male',
            'genes': 'All',
            'rarity': 'all',
            'effectTypes': "frame-shift",
            'presentInChild': 'autism only',
            'variantTypes': 'CNV,del,ins,sub',
            'presentInParent': 'neither',
            'transmittedStudies': 'w1202s766e611',
            'familyPhenoMeasure': "pheno_common.verbal_iq",
            'familyPhenoMeasureMin': 49,
            'familyPhenoMeasureMax': 50,
        }

        response = self.client.post(url, request, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEquals('3', response.data['count'])

    def test_verbal_iq_from0_to50_with_family_ids(self):
        url = "/api/ssc_query_variants_preview"
        request = {
            'gene_set_phenotype': 'autism',
            'denovoStudies': 'ALL SSC',
            'families': 'familyIds',
            'familyIds': '11480,11518',
            'gender': 'female,male',
            'genes': 'All',
            'rarity': 'all',
            'effectTypes': "frame-shift",
            'presentInChild': 'autism only',
            'variantTypes': 'CNV,del,ins,sub',
            'presentInParent': 'neither',
            'transmittedStudies': 'w1202s766e611',
            'familyPhenoMeasure': 'pheno_common.verbal_iq',
            'familyPhenoMeasureMin': 0,
            'familyPhenoMeasureMax': 50,
        }

        response = self.client.post(url, request, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEquals('2', response.data['count'])

    def test_verbal_iq_from49_to50_with_family_ids(self):
        url = "/api/ssc_query_variants_preview"
        request = {
            'gene_set_phenotype': 'autism',
            'denovoStudies': 'ALL SSC',
            'families': 'familyIds',
            'familyIds': '13504',
            'gender': 'female,male',
            'genes': 'All',
            'rarity': 'all',
            'effectTypes': "frame-shift",
            'presentInChild': 'autism only',
            'variantTypes': 'CNV,del,ins,sub',
            'presentInParent': 'neither',
            'transmittedStudies': 'w1202s766e611',
            'familyPhenoMeasure': 'pheno_common.verbal_iq',
            'familyPhenoMeasureMin': 49,
            'familyPhenoMeasureMax': 50,
        }

        response = self.client.post(url, request, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEquals('1', response.data['count'])
