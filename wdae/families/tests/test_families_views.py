'''
Created on Mar 23, 2016

@author: lubo
'''
from rest_framework.test import APITestCase
from pprint import pprint


class Test(APITestCase):

    def test_families_counter_view_with_pheno_measure(self):
        url = "/api/v2/families/counter"
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

        self.assertEquals(36, data['unaffected']['families'])
        self.assertEquals(19, data['unaffected']['male'])
        self.assertEquals(17, data['unaffected']['female'])

    def test_families_counter_view_combined_filter(self):
        url = "/api/v2/families/counter"
        data = {
            'familyPhenoMeasure': 'non_verbal_iq',
            'familyPhenoMeasureMin': 0,
            'familyPhenoMeasureMax': 24,
            'familyQuadTrio': 'quad',
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        data = response.data

        self.assertEquals(23, data['autism']['families'])
        self.assertEquals(22, data['autism']['male'])
        self.assertEquals(1, data['autism']['female'])

        self.assertEquals(23, data['unaffected']['families'])
        self.assertEquals(11, data['unaffected']['male'])
        self.assertEquals(12, data['unaffected']['female'])

    def test_families_empty_filters(self):
        url = "/api/v2/families/counter"
        data = {
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        data = response.data

        self.assertEquals(2867, data['autism']['families'])      # 2867
        self.assertEquals(2471, data['autism']['male'])          # 2477
        self.assertEquals(389, data['autism']['female'])         # 390

        self.assertEquals(2703, data['unaffected']['families'])  # 2703
        self.assertEquals(1285, data['unaffected']['male'])      # 1285
        self.assertEquals(1418, data['unaffected']['female'])    # 1418

    def test_families_pheno_measure_filters(self):
        url = "/api/v2/families/counter"
        data = {
            'phenoMeasure': 'non_verbal_iq',
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        data = response.data

        pprint(data)

        self.assertEquals(2763, data['autism']['families'])
        self.assertEquals(2382, data['autism']['male'])
        self.assertEquals(374, data['autism']['female'])

        self.assertEquals(2607, data['unaffected']['families'])
        self.assertEquals(1232, data['unaffected']['male'])
        self.assertEquals(1375, data['unaffected']['female'])

    def test_families_pheno_measure_filters_normalized(self):
        url = "/api/v2/families/counter"
        data = {
            'phenoMeasure': 'head_circumference',
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        data = response.data

        pprint(data)

        self.assertEquals(2734, data['autism']['families'])
        self.assertEquals(2356, data['autism']['male'])
        self.assertEquals(371, data['autism']['female'])

        self.assertEquals(2580, data['unaffected']['families'])
        self.assertEquals(1220, data['unaffected']['male'])
        self.assertEquals(1360, data['unaffected']['female'])

    def test_family_ids_counter(self):
        url = "/api/v2/families/counter"
        data = {
            u'families': u'familyIds',
            u'familyIds': u'3084 \n11241 \n11241 \n11558 \n11810 \n11944'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        data = response.data

        pprint(data)

        self.assertEquals(4, data['autism']['families'])

    def test_family_ids_counter_with_commas(self):
        url = "/api/v2/families/counter"
        data = {
            u'families': u'familyIds',
            u'familyIds': u'3084, \n11241, \n11241, \n11558, \n11810, \n11944,'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        data = response.data

        pprint(data)

        self.assertEquals(4, data['autism']['families'])

    def test_family_ids_counter_with_spaces(self):
        url = "/api/v2/families/counter"
        data = {
            u'families': u'familyIds',
            u'familyIds': u'\n11241, \t\n11558 \t, \n11810\t\t, \n11944,'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        data = response.data

        pprint(data)

        self.assertEquals(4, data['autism']['families'])
