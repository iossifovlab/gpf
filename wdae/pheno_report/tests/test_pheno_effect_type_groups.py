'''
Created on Nov 16, 2015

@author: lubo
'''

from pheno_report.views import PhenoEffectTypeGroups
from users_api.tests.base_tests import BaseAuthenticatedUserTest


def count_iterable(iterable):
    for num, _it in enumerate(iterable):
        pass
    return num + 1


class Test(BaseAuthenticatedUserTest):

    def test_list_effect_type_groups(self):
        url = "/api/v2/pheno_reports/effect_type_groups"

        response = self.client.get(url)
        self.assertEqual(200, response.status_code)

    def test_each_effect_type_group(self):
        for et in PhenoEffectTypeGroups.effect_type_groups:
            url = "/api/v2/pheno_reports"
            data = {
                'denovoStudies': 'ALL SSC',
                'transmittedStudies': 'w1202s766e611',
                'presentInParent': "father only",
                'geneSyms': "POGZ",
                'phenoMeasure': 'ssc_commonly_used.head_circumference',
                'effectTypeGroups': et,
            }
            response = self.client.post(url, data, format='json')
            self.assertEqual(200, response.status_code)
            data = response.data['data']
            self.assertEquals(2, len(data))
            self.assertEquals(et, data[0][0])
            self.assertEquals(et, data[1][0])
