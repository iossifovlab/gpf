'''
Created on Oct 23, 2015

@author: lubo
'''
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

    def test_verbal_iq_from0_to50(self):
        url = "/api/ssc_query_variants_preview"
        request = {
            'gene_set_phenotype': 'autism',
            'denovoStudies': 'ALL SSC',
            'families': 'familyIds',
            # 'familyIds': '11000,11110,12119,11071,11077,14673',
            'gender': 'female,male',
            'genes': 'All',
            'rarity': 'all',
            'effectTypes': "frame-shift",
            'presentInChild': 'autism only',
            'variantTypes': 'CNV,del,ins,sub',
            'presentInParent': 'neither',
            'transmittedStudies': 'w1202s766e611',
            'familyPhenoMeasure': "verbal_iq",
            'familyPhenoMeasureMin': 0,
            'familyPhenoMeasureMax': 50,
        }

        response = self.client.post(url, request, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.data['count'])
        self.assertEqual('43', response.data['count'])

    def test_verbal_iq_from49_to50(self):
        url = "/api/ssc_query_variants_preview"
        request = {
            'gene_set_phenotype': 'autism',
            'denovoStudies': 'ALL SSC',
            'families': 'familyIds',
            # 'familyIds': '11000,11110,12119',
            'gender': 'female,male',
            'genes': 'All',
            'rarity': 'all',
            'effectTypes': "frame-shift",
            'presentInChild': 'autism only',
            'variantTypes': 'CNV,del,ins,sub',
            'presentInParent': 'neither',
            'transmittedStudies': 'w1202s766e611',
            'familyPhenoMeasure': "verbal_iq",
            'familyPhenoMeasureMin': 49,
            'familyPhenoMeasureMax': 50,
        }

        response = self.client.post(url, request, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.data['count'])
        self.assertEquals('3', response.data['count'])

    def test_verbal_iq_from0_to50_with_family_ids(self):
        url = "/api/ssc_query_variants_preview"
        request = {
            'gene_set_phenotype': 'autism',
            'denovoStudies': 'ALL SSC',
            'families': 'familyIds',
            'familyIds': '11480,11518',
            'gender': 'female,male',
            'genes': 'All',
            'rarity': 'all',
            'effectTypes': "frame-shift",
            'presentInChild': 'autism only',
            'variantTypes': 'CNV,del,ins,sub',
            'presentInParent': 'neither',
            'transmittedStudies': 'w1202s766e611',
            'familyPhenoMeasure': 'verbal_iq',
            'familyPhenoMeasureMin': 0,
            'familyPhenoMeasureMax': 50,
        }

        response = self.client.post(url, request, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.data['count'])
        self.assertEquals('2', response.data['count'])

    def test_verbal_iq_from49_to50_with_family_ids(self):
        url = "/api/ssc_query_variants_preview"
        request = {
            'gene_set_phenotype': 'autism',
            'denovoStudies': 'ALL SSC',
            'families': 'familyIds',
            'familyIds': '13504',
            'gender': 'female,male',
            'genes': 'All',
            'rarity': 'all',
            'effectTypes': "frame-shift",
            'presentInChild': 'autism only',
            'variantTypes': 'CNV,del,ins,sub',
            'presentInParent': 'neither',
            'transmittedStudies': 'w1202s766e611',
            'familyPhenoMeasure': 'verbal_iq',
            'familyPhenoMeasureMin': 49,
            'familyPhenoMeasureMax': 50,
        }

        response = self.client.post(url, request, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.data['count'])
        self.assertEquals('1', response.data['count'])
