'''
Created on Mar 23, 2016

@author: lubo
'''
from rest_framework.test import APITestCase
from pprint import pprint


class Test(APITestCase):

    def test_families_counter_view_with_pheno_measure(self):
        url = "/api/v2/ssc_dataset_families/counter"
        data = {
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

        self.assertEquals(29, data['unaffected']['families'])
        self.assertEquals(16, data['unaffected']['male'])
        self.assertEquals(16, data['unaffected']['female'])

    def test_families_counter_view_combined_filter(self):
        url = "/api/v2/ssc_dataset_families/counter"
        data = {
            'familyPhenoMeasure': 'pheno_common.non_verbal_iq',
            'familyPhenoMeasureMin': 0,
            'familyPhenoMeasureMax': 24,
            'familyQuadTrio': 'quad',
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        data = response.data

        self.assertEquals(0, data['autism']['families'])
        self.assertEquals(0, data['autism']['male'])
        self.assertEquals(0, data['autism']['female'])

        self.assertEquals(0, data['unaffected']['families'])
        self.assertEquals(0, data['unaffected']['male'])
        self.assertEquals(0, data['unaffected']['female'])

    def test_families_empty_filters(self):
        url = "/api/v2/ssc_dataset_families/counter"
        data = {
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        data = response.data

        self.assertEquals(2860, data['autism']['families'])
        self.assertEquals(2471, data['autism']['male'])
        self.assertEquals(389, data['autism']['female'])

        self.assertEquals(2380, data['unaffected']['families'])
        self.assertEquals(1190, data['unaffected']['male'])
        self.assertEquals(1330, data['unaffected']['female'])

    def test_families_counter_with_wrong_family_id(self):
        url = "/api/v2/ssc_dataset_families/counter"
        data = {
            'familyIds': '1100',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)

    def test_families_cnv_quads(self):
        url = "/api/v2/ssc_dataset_families/counter"
        data = {
            'familyQuadTrio': 'quad',
            'familyStudyType': 'cnv',
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        data = response.data

        pprint(data)
        self.assertEquals(2225, data['autism']['families'])
        self.assertEquals(
            data['autism']['families'],
            data['autism']['male'] + data['autism']['female']
        )

        self.assertEquals(2225, data['unaffected']['families'])  # 2703
        self.assertEquals(
            data['unaffected']['families'],
            data['unaffected']['male'] + data['unaffected']['female']
        )
