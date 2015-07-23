'''
Created on Jul 23, 2015

@author: lubo
'''
import unittest
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework import status


class Test(APITestCase):

    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass()
        
        
        User = get_user_model()
        u = User.objects.create(email="admin@example.com",
                                first_name="First",
                                last_name="Last",
                                is_staff=True,
                                is_active=True,
                                researcher_id="0001000")
        u.set_password("secret")
        u.save()

        cls.user = u
        _token = Token.objects.get_or_create(user=u)
        cls.user.save()
        
    def setUp(self):
        super(Test, self).setUpClass()



    def tearDown(self):
        pass


    def test_authenticated(self):
        region = "1:151377900-151378500"
        data = {
            "effectTypes": "Nonsense,Frame-shift,Splice-site",
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "None",
            "presentInChild": "autism only",
            "gender": "male,female",
            "geneRegion": region,
        }


        self.client.login(email='admin@example.com', password='secret')
        token = Token.objects.get(user__email='admin@example.com')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        
        url = '/api/ssc_query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_unauthenticated(self):
        region = "1:151377900-151378500"
        data = {
            "effectTypes": "Nonsense,Frame-shift,Splice-site",
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "None",
            "presentInChild": "autism only",
            "gender": "male,female",
            "geneRegion": region,
        }


        self.client.logout()
        
        url = '/api/ssc_query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()