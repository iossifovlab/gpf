'''
Created on Nov 16, 2015

@author: lubo
'''
from pprint import pprint
import unittest

from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

from pheno_report.views import PhenoEffectTypeGroups


def count_iterable(iterable):
    for num, _it in enumerate(iterable):
        pass
    return num + 1


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

    @classmethod
    def tearDownClass(cls):
        super(Test, cls).tearDownClass()
        cls.user.delete()

    def setUp(self):
        super(Test, self).setUpClass()
        self.client.login(email='admin@example.com', password='secret')
        token = Token.objects.get(user__email='admin@example.com')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def tearDown(self):
        pass

    def test_list_effect_type_groups(self):
        url = "/api/v2/pheno_reports/effect_type_groups"

        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        pprint(response.data)

    def test_each_effect_type_group(self):
        for et in PhenoEffectTypeGroups.effect_type_groups:
            url = "/api/v2/pheno_reports"
            data = {
                'denovoStudies': 'ALL SSC',
                'transmittedStudies': 'w1202s766e611',
                'presentInParent': "father only",
                'geneSyms': "POGZ",
                'phenoMeasure': 'ssc_commonly_used.head_circumference',
                'effectTypeGroups': et,
            }
            response = self.client.post(url, data, format='json')
            self.assertEqual(200, response.status_code)
            data = response.data['data']
            pprint(data)
            self.assertEquals(2, len(data))
            self.assertEquals(et, data[0][0])
            self.assertEquals(et, data[1][0])

if __name__ == "__main__":
    unittest.main()
