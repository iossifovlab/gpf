'''
Created on May 27, 2016

@author: lubo
'''
from rest_framework.test import APITestCase
from pprint import pprint


class Test(APITestCase):

    @staticmethod
    def with_hit(data):
        return data[7]

    @staticmethod
    def without_hit(data):
        return data[8]

    def test_all_with_lgds_non_verbal_iq(self):
        url = "/api/v2/pheno_reports"

        data = {u'phenoMeasure': u'non_verbal_iq',
                u'denovoStudies': u'ALL SSC',
                u'families': u'Advanced',
                u'gene_set_phenotype': u'autism',
                u'normalizedBy': u'',
                u'familyQuadTrio': u'All',
                u'genes': u'All',
                u'familyPhenoMeasureMin': 8,
                u'familyPhenoMeasureMax': 162,
                u'familySibGender': u'All',
                u'effectTypeGroups': u'LGDs',
                u'familyPrbGender': u'All',
                u'presentInParent': u'neither',
                u'familyStudyType': u'All',
                u'familyRace': u'All',
                u'familyPhenoMeasure': u'non_verbal_iq'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        result = response.data['data']
        pprint(result)

        with_hit_male = self.with_hit(result[0])
        without_hit_male = self.without_hit(result[0])
        self.assertEquals(2388, 7 + with_hit_male + without_hit_male)  # 2477

        with_hit_female = self.with_hit(result[1])
        without_hit_female = self.without_hit(result[1])
        self.assertEquals(375, 1 + with_hit_female + without_hit_female)  # 390
