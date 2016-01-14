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

    def test_chrome_X_pedigree(self):
        data = {
            'gene_set_phenotype': 'autism',
            'denovoStudies': 'ALL SSC',
            'families': 'familyIds',
            'familyIds': '11002',
            'gender': 'female,male',
            'genes': 'Gene Symbols',
            'rarity': 'all',
            'effectTypes': 'frame-shift,nonsense,splice-site',
            'presentInChild': 'autism and unaffected,autism only',
            'variantTypes': 'CNV,del,ins,sub',
            'presentInParent': 'father only,mother and father,mother only',
            'transmittedStudies': 'w1202s766e611',
            'limit': 2000,
            'geneSyms': 'DGKK'}

        url = '/api/ssc_query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('1', response.data['count'])
        row = response.data['rows'][0]
        pedigree = json.loads(row[-2])
        print(pedigree)
        m = pedigree[1]
        print(m)
        self.assertEqual(0, m[0][-1])
        self.assertEqual(0, m[1][-1])
        self.assertEqual(0, m[2][-1])
        self.assertEqual(0, m[3][-1])


if __name__ == "__main__":
    unittest.main()
