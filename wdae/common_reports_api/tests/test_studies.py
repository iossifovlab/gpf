'''
Created on May 22, 2017

@author: lubo
'''
from rest_framework.test import APITestCase
from common_reports_api.studies import get_transmitted_studies_names,\
    get_denovo_studies_names


class ApiTest(APITestCase):

    def test_transmitted_studies_list(self):
        response = self.client.get(
            '/api/v3/common_reports/transmitted_studies')
        self.assertEqual(
            response.data,
            {"transmitted_studies": get_transmitted_studies_names()})

#     def test_report_studies(self):
#         response = self.client.get(
#             '/api/v3/common_reports/report_studies')
#         data = {"report_studies": get_denovo_studies_names() +
#                 get_transmitted_studies_names()}
#         self.assertEqual(response.data, data)

    def test_denovo_studies_list(self):
        data = get_denovo_studies_names()
        response = self.client.get(
            '/api/v3/common_reports/denovo_studies')
        self.assertEqual(response.data, {'denovo_studies': data})
