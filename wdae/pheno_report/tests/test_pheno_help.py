'''
Created on Oct 14, 2016

@author: lubo
'''

from rest_framework.test import APITestCase


class Test(APITestCase):

    def test_measures_help(self):
        url = \
            "/api/v2/pheno_reports/measures_help?instrument=ssc_commonly_used"
        response = self.client.get(url, format='json')
        self.assertEqual(200, response.status_code)

        print(response.data)
