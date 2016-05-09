'''
Created on Nov 16, 2015

@author: lubo
'''
from pprint import pprint
import unittest

from rest_framework.test import APITestCase

from pheno.views import PhenoEffectTypeGroups


def count_iterable(iterable):
    for num, _it in enumerate(iterable):
        pass
    return num + 1


class Test(APITestCase):

    def test_list_effect_type_groups(self):
        url = "/api/v2/pheno_reports/effect_type_groups"

        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        pprint(response.data)

    def test_each_effect_type_group(self):
        for et in PhenoEffectTypeGroups.effect_type_groups:
            url = "/api/v2/pheno_reports"
            data = {
                'denovoStudies': 'ALL SSC',
                'transmittedStudies': 'w1202s766e611',
                'presentInParent': "father only",
                'geneSyms': "POGZ",
                'phenoMeasure': 'head_circumference',
                'effectTypeGroups': et,
            }
            response = self.client.post(url, data, format='json')
            self.assertEqual(200, response.status_code)
            data = response.data['data']
            pprint(data)
            self.assertEquals(2, len(data))
            self.assertEquals(et, data[0][0])
            self.assertEquals(et, data[1][0])

if __name__ == "__main__":
    unittest.main()
