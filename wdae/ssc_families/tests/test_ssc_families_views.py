'''
Created on Mar 23, 2016

@author: lubo
'''
from rest_framework.test import APITestCase


class Test(APITestCase):

    def test_families_counter_view_with_pheno_measure(self):
        url = "/api/v2/ssc_dataset_families/counter"
        data = {
            'familyPhenoMeasure': 'non_verbal_iq',
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
            'familyPhenoMeasure': 'non_verbal_iq',
            'familyPhenoMeasureMin': 0,
            'familyPhenoMeasureMax': 24,
            'familyQuadTrio': 'quad',
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        data = response.data

        self.assertEquals(5, data['autism']['families'])
        self.assertEquals(5, data['autism']['male'])
        self.assertEquals(0, data['autism']['female'])

        self.assertEquals(5, data['unaffected']['families'])
        self.assertEquals(3, data['unaffected']['male'])
        self.assertEquals(2, data['unaffected']['female'])

    def test_families_empty_filters(self):
        url = "/api/v2/ssc_dataset_families/counter"
        data = {
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        data = response.data

        self.assertEquals(2860, data['autism']['families'])      # 2867
        self.assertEquals(2471, data['autism']['male'])          # 2477
        self.assertEquals(389, data['autism']['female'])         # 390

        self.assertEquals(2380, data['unaffected']['families'])  # 2703
        self.assertEquals(1190, data['unaffected']['male'])      # 1285
        self.assertEquals(1330, data['unaffected']['female'])    # 1418

    def test_families_counter_with_wrong_family_id(self):
        url = "/api/v2/ssc_dataset_families/counter"
        data = {
            'familyIds': '1100',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
