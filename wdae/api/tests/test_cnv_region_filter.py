'''
Created on Jan 4, 2016

@author: lubo
'''
import unittest
from rest_framework.test import APITestCase
from rest_framework import status


class Test(APITestCase):

    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass()
        from django.contrib.auth import get_user_model
        from rest_framework.authtoken.models import Token

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
        Token.objects.get_or_create(user=u)
        cls.user.save()

    @classmethod
    def tearDownClass(cls):
        super(Test, cls).tearDownClass()
        cls.user.delete()

    def setUp(self):
        from rest_framework.authtoken.models import Token
        APITestCase.setUp(self)

        self.client.login(email='admin@example.com', password='secret')
        token = Token.objects.get(user__email='admin@example.com')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_cnv_region(self):
        data = {
            'geneRegion': '1:240530000-242300000',
            "effectTypes": "CNV+",
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "None",
            "presentInChild": "autism only",
            "gender": "male,female",
        }

        url = '/api/ssc_query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('2', response.data['count'])

    def test_all_region(self):
        data = {
            'geneRegion': '1:240530000-242300000',
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "None",
            "presentInChild": "autism only",
            "gender": "male,female",
        }

        url = '/api/ssc_query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('4', response.data['count'])

    def test_all_effects_region_and_gene(self):
        data = {
            "geneSyms": "WDR64",
            'geneRegion': '1:240530000-242300000',
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "None",
            "presentInChild": "autism only",
            "gender": "male,female",
        }

        url = '/api/ssc_query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('2', response.data['count'])


if __name__ == "__main__":
    unittest.main()
