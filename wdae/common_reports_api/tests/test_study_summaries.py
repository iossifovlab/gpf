'''
Created on May 25, 2017

@author: lubo
'''
from users_api.tests.base_tests import BaseAuthenticatedUserTest
from rest_framework import status


class Test(BaseAuthenticatedUserTest):

    URL = "/api/v3/common_reports/studies_summaries"

    def test_get_summaries(self):
        response = self.client.get(self.URL)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        data = response.data

        self.assertIn('summaries', data)
        self.assertIn('columns', data)

        self.assertEquals(35, len(data['summaries']))
        self.assertEquals(11, len(data['columns']))
