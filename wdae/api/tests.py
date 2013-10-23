"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from rest_framework.test import APIClient

from rest_framework import status
from rest_framework.test import APITestCase

class FamiliesTest(APITestCase):
    client = APIClient()
            
    def test_families_get(self):        
        response=self.client.get('/api/families/DalyWE2012')
                
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data=response.data
        self.assertEqual(data['study'],'DalyWE2012')
        
    def test_families_get_filter(self):        
        response=self.client.get('/api/families/DalyWE2012')
                
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data=response.data
        self.assertEqual(data['study'],'DalyWE2012')
        self.assertEqual(len(data['families']),174)
        
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

