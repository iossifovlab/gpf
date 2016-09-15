'''
Created on Jul 6, 2016

@author: lubo
'''
from rest_framework.test import APITestCase
from pprint import pprint


class Test(APITestCase):

    def test_families_counter_view_with_pheno_measure(self):
        url = "/api/v2/ssc_pheno_families/counter"
        data = {
            'phenoMeasure': 'pheno_common.non_verbal_iq',
            'familyPhenoMeasure': 'pheno_common.non_verbal_iq',
            'familyPhenoMeasureMin': 0,
            'familyPhenoMeasureMax': 24,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        data = response.data

        self.assertEquals(34, data['autism']['families'])
        self.assertEquals(32, data['autism']['male'])
        self.assertEquals(2, data['autism']['female'])

        self.assertEquals(0, data['unaffected']['families'])
        self.assertEquals(0, data['unaffected']['male'])
        self.assertEquals(0, data['unaffected']['female'])

    def test_family_counters_ivans_test_case(self):
        url = "/api/v2/ssc_pheno_families/counter"
        data = {
            'phenoMeasure': 'pheno_common.non_verbal_iq',
            "familyRace": "All",
            "familyPhenoMeasure": "ssc_commonly_used.vabs_ii_motor_skills",
            "familyPhenoMeasureMin": 0,
            "familyPhenoMeasureMax": 134,
            "familyStudyType": "All",
            "familyStudies": "All"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        data = response.data

        pprint(data)

        self.assertEquals(131, data['autism']['female'])
        self.assertEquals(858, data['autism']['male'])
        self.assertEquals(989, data['autism']['families'])
