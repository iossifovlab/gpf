'''
Created on Dec 11, 2015

@author: lubo
'''
import unittest
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model


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
        Token.objects.get_or_create(user=u)
        cls.user.save()

    @classmethod
    def tearDownClass(cls):
        super(Test, cls).tearDownClass()
        cls.user.delete()

    def setUp(self):
        APITestCase.setUp(self)
        self.client.login(email='admin@example.com', password='secret')
        token = Token.objects.get(user__email='admin@example.com')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_rvis_rank_in_autism_zero_genes(self):
        data = {
            "geneWeight": "RVIS_rank",
            "geneWeightMin": 1.0,
            "geneWeightMax": 5.0,
            "denovoStudies": "ALL WHOLE EXOME",
            "phenoType": "autism",
            "gender": "female,male",
        }

        url = '/api/query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('19', response.data['count'])

    def test_rvis_rank_zero_to_one_in_autism(self):
        data = {
            "geneWeight": "RVIS",
            "geneWeightMin": 0.0,
            "geneWeightMax": 0.0,
            "denovoStudies": "ALL WHOLE EXOME",
            "phenoType": "autism",
            "gender": "female,male",
        }

        url = '/api/query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('33', response.data['count'])

    def test_ssc_rest_call_by_gene_weight_rvis_25_to_30(self):
        data = {
            "geneWeight": "RVIS",
            "geneWeightMin": 25,
            "geneWeightMax": 30,
            "gender": "female,male",
            'effectTypes':
            'frame-shift,nonsense,splice-site',
            'presentInChild': 'autism only',
            'presentInParent': 'father only,mother and father,'
            'mother only,neither',
            'rarity': 'ultraRare',
        }

        url = '/api/ssc_query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('15', response.data['count'])

    def test_ssc_rest_call_by_gene_syms(self):
        data = {
            'denovoStudies': 'ALL SSC',
            'geneSyms': 'AHNAK2,MUC16',
            'gender': 'female,male',
            'rarity': 'ultraRare',
            'effectTypes':
            'frame-shift,nonsense,splice-site',
            'presentInChild': 'autism only',
            'presentInParent': 'father only,mother and father,'
            'mother only,neither',
            'transmittedStudies': 'w1202s766e611',
        }

        url = '/api/ssc_query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('15', response.data['count'])

    def test_sd_rest_call_by_gene_weight_rvis_25_to_30(self):

        data = {
            "geneWeight": "RVIS",
            "geneWeightMin": 25,
            "geneWeightMax": 30,
            "gender": "female,male",
            'effectTypes': 'missense,synonymous',
            'phenoType': 'autism,unaffected',
        }

        url = '/api/sd_query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('19', response.data['count'])

    def test_sd_rest_call_by_gene_syms(self):

        data = {
            'gender': 'female,male',
            'effectTypes': 'missense,synonymous',
            'phenoType': 'autism,unaffected',
            'variantTypes': 'del,ins,sub',
            'geneSyms': 'AHNAK2,MUC16'
        }

        url = '/api/sd_query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('19', response.data['count'])

if __name__ == "__main__":
    unittest.main()
