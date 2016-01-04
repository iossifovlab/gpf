'''
Created on Jan 4, 2016

@author: lubo
'''
import unittest
from rest_framework.test import APITestCase
from rest_framework import status
import json


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

    def test_cnv_plus_3(self):
        data = {
            "geneSyms": "PLD5",
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
        row = response.data['rows'][0]
        pedigree = json.loads(row[-2])
        prb = pedigree[1][2]
        self.assertEqual(3, prb[-1])

    def test_cnv_minus_1(self):
        data = {
            "geneSyms": "NRXN1",
            "effectTypes": "CNV-",
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "None",
            "presentInChild": "autism only",
            "gender": "male,female",
        }

        url = '/api/ssc_query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('3', response.data['count'])
        row = response.data['rows'][0]
        pedigree = json.loads(row[-2])
        prb = pedigree[1][2]
        self.assertEqual(1, prb[-1])

    def test_lgds(self):
        data = {
            "effectTypes": "nonsense,frame-shift,splice-site",
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "None",
            "presentInChild": "autism only",
            "gender": "male,female",
        }

        url = '/api/ssc_query_variants_preview'

        response = self.client.post(url, data, format='json')
        for row in response.data['rows']:
            print(row)
            pedigree = json.loads(row[-2])
            prb = pedigree[1][2]
            self.assertTrue(prb[-1] < 3)

if __name__ == "__main__":
    unittest.main()
