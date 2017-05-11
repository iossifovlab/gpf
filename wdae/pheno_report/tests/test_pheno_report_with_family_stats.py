'''
Created on May 27, 2016

@author: lubo
'''
from users_api.tests.base_tests import BaseAuthenticatedUserTest


class Test(BaseAuthenticatedUserTest):

    @staticmethod
    def with_hit(data):
        return data[7]

    @staticmethod
    def without_hit(data):
        return data[8]

    def test_all_with_lgds_non_verbal_iq(self):
        url = "/api/v2/pheno_reports"

        data = {
            u'phenoMeasure': u'pheno_common.non_verbal_iq',
            u'denovoStudies': u'ALL SSC',
            u'effectTypeGroups': u'LGDs',
            u'presentInParent': u'neither',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        result = response.data['data']

        url = "/api/v2/ssc_pheno_families/counter"
        data = {
            'phenoMeasure': 'pheno_common.non_verbal_iq',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)

        family_stats = response.data

        with_hit_male = self.with_hit(result[0])
        without_hit_male = self.without_hit(result[0])
        self.assertEquals(family_stats['autism']['male'],
                          with_hit_male + without_hit_male)

        with_hit_female = self.with_hit(result[1])
        without_hit_female = self.without_hit(result[1])
        self.assertEquals(family_stats['autism']['female'],
                          with_hit_female + without_hit_female)  # 390

    def test_all_with_lgds_non_head_circumference(self):
        url = "/api/v2/pheno_reports"

        data = {
            u'phenoMeasure': u'ssc_commonly_used.head_circumference',
            u'denovoStudies': u'ALL SSC',
            u'effectTypeGroups': u'LGDs',
            u'presentInParent': u'neither',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        result = response.data['data']

        url = "/api/v2/ssc_pheno_families/counter"
        data = {
            'phenoMeasure': 'ssc_commonly_used.head_circumference',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)

        family_stats = response.data

        with_hit_male = self.with_hit(result[0])
        without_hit_male = self.without_hit(result[0])
        self.assertEquals(family_stats['autism']['male'],
                          with_hit_male + without_hit_male)

        with_hit_female = self.with_hit(result[1])
        without_hit_female = self.without_hit(result[1])
        self.assertEquals(family_stats['autism']['female'],
                          with_hit_female + without_hit_female)  # 390
