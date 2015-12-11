'''
Created on Oct 23, 2015

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
        _token = Token.objects.get_or_create(user=u)
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

    def testName(self):
        url = "/api/ssc_query_variants_preview"
        request = {
            'gene_set_phenotype': 'autism',
            'denovoStudies': 'ALL SSC',
            'families': 'familyIds',
            'familyIds': '11110',
            'gender': 'female,male',
            'genes': 'All',
            'rarity': 'all',
            'effectTypes':
            "frame-shift,intergenic,intron,missense,non-coding,"
            "no-frame-shift,nonsense,splice-site,synonymous,noEnd,"
            "noStart,3'UTR,5'UTR,CNV+,CNV-,3'UTR,3'UTR-intron,5'UTR,"
            "5'UTR-intron",
            'presentInChild': 'autism only',
            'variantTypes': 'CNV,del,ins,sub',
            'presentInParent': 'father only,mother and father,mother only,'
            'neither',
            'transmittedStudies': 'w1202s766e611'
        }

        response = self.client.post(url, request, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # FIXME

if __name__ == "__main__":
    unittest.main()
