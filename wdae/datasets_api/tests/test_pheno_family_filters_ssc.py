'''
Created on Mar 25, 2017

@author: lubo
'''
from rest_framework.test import APITestCase
from rest_framework import status
from pprint import pprint
from django.contrib.auth import get_user_model


class Test(APITestCase):

    @classmethod
    def setUpClass(cls):
        super(Test, cls).setUpClass()

        User = get_user_model()
        u = User.objects.create(
            email="admin@example.com",
            first_name="First",
            last_name="Last",
            is_staff=True,
            is_active=True,
            researcher_id="0001000")
        u.set_password("secret")
        u.save()

        cls.user = u
        cls.user.save()

    @classmethod
    def tearDownClass(cls):
        super(Test, cls).tearDownClass()
        cls.user.delete()

    def setUp(self):
        APITestCase.setUp(self)
        self.client.login(
            email='admin@example.com', password='secret')

    def test_pheno_family_filters(self):
        url = '/api/v3/genotype_browser/preview'
        data = {
            'effectTypes': ['Frame-shift', 'Nonsense', 'Splice-site'],
            "gender": ["female", "male"],
            "presentInChild": [
                "affected and unaffected",
                "affected only",
            ],
            "presentInParent": [
                "neither"
            ],
            "variantTypes": [
                "CNV", "del", "ins", "sub",
            ],
            "datasetId": "SSC",
            "pedigreeSelector": {
                'id': "phenotype",
                "checkedValues": ["autism", "unaffected"]
            },
            "phenoFilters": [
                {
                    'measureType': 'categorical',
                    'measure': 'pheno_common.race',
                    'role': 'prb',
                    'selection': ['native-hawaiian', 'white'],
                },
                {
                    'measureType': 'continuous',
                    'measure': 'pheno_common.non_verbal_iq',
                    'role': 'prb',
                    'mmin': 80,
                    'mmax': 80
                }
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        pprint(data)
        self.assertEquals('5', data['count'])
