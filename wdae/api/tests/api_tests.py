from rest_framework.test import APIClient

from django.core.urlresolvers import resolve

from django.shortcuts import render

from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory

from api.views import gene_sets_list, denovo_studies_list, enrichment_test
from api.studies import get_denovo_studies_names
from api.enrichment import enrichment_results

class FamiliesApiTest(APITestCase):

    def setUp(self):
        self.factory = APIRequestFactory()

    @staticmethod
    def generate_enrichment_response(self, url):
        request = self.factory.get(url)
        response = enrichment_test(request)
        response.render()
        return response

    def test_enrichment_test(self):
        # Testing the best case
        TEST_DATA = enrichment_results('allWE', 'w873e374s322', 'main', 'ChromatinModifiers')
        url = '/api/enrichment_test?dst_name=allWE&tst_name=w873e374s322&gt_name=main&gs_name=ChromatinModifiers'
        self.assertEqual(FamiliesApiTest.generate_enrichment_response(self, url).data, TEST_DATA)
        # Testing missing arguments
        url_missing_dst_name = '/api/enrichment_test?tst_name=w873e374s322&gt_name=main&gs_name=ChromatinModifiers';
        url_missing_tst_name = '/api/enrichment_test?dst_name=allWE&gt_name=main&gs_name=ChromatinModifiers'
        url_missing_gt_name = '/api/enrichment_test?dst_name=allWE&tst_name=w873e374s322&gs_name=ChromatinModifiers'
        url_missing_gs_name = '/api/enrichment_test?dst_name=allWE&tst_name=w873e374s322&gt_name=main'

        self.assertEqual(FamiliesApiTest.generate_enrichment_response(self, url_missing_dst_name).data, None)
        self.assertEqual(FamiliesApiTest.generate_enrichment_response(self, url_missing_tst_name).data, None)
        self.assertEqual(FamiliesApiTest.generate_enrichment_response(self, url_missing_gt_name).data, None)
        self.assertEqual(FamiliesApiTest.generate_enrichment_response(self, url_missing_gs_name).data, None)

    def test_gene_sets_list(self):
        TEST_DATA = {"gene_sets" : [{'label' : 'Main', 'val' : 'main', 'conf' : ['[[[', 'key', ']]]', '(((' , 'count', '))):', "desc"]},
                    {'label' : 'GO', 'val' : 'GO' ,'conf' : ['key', 'count']},
                    {'label' : 'Disease', 'val' : 'disease' ,'conf' : ['key', 'count']},
                    {'label' : 'Denovo', 'val' : 'denovo' ,'conf' : ['---', 'key', '---', 'desc', '---', 'count']}]}

        request = self.factory.get('/api/gene_sets')
        response = gene_sets_list(request)
        response.render()
        self.assertEqual(response.data, TEST_DATA)        

    def test_denovo_studies_list(self):
        data = get_denovo_studies_names()
        request = self.factory.get('/api/denovo_studies')
        response = denovo_studies_list(request)
        response.render()
        self.assertEqual(response.data, {'denovo_studies' : data})

    def test_families_get(self):
        response = self.client.get('/api/families/DalyWE2012')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data['study'], 'DalyWE2012')

    def test_families_get_filter(self):
        response = self.client.get('/api/families/DalyWE2012')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data['study'], 'DalyWE2012')
        self.assertEqual(len(data['families']), 174)

#     def test_families_post(self):
#         data={'studies':['DalyWE2012','EichlerTG2012']}
#         response=self.client.post('/api/families?filter="A"', data, format='json')
#
#         self.assertEqual(response.status_code, status.HTTP_200_OK)


# class GetVariantsTest(APITestCase):
#     client = APIClient()
#
#     def test_get_denovo_simple(self):
#         query={"denovoStudies":["DalyWE2012", "EichlerTG2012"]}
#         response=self.client.post("/api/get_variants_csv/",data=query,content_type='application/json')
#         self.assertEqual(response.status_code,status.HTTP_200_OK)
#
