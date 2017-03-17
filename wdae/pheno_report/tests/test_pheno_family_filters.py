'''
Created on Feb 29, 2016

@author: lubo
'''
from rest_framework.test import APITestCase
import preloaded.register
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token


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

    @staticmethod
    def pos_count(effect, data):
        for vals in data:
            if vals[0] == effect:
                return vals[7]
        return None

    @staticmethod
    def neg_count(effect, data):
        for vals in data:
            if vals[0] == effect:
                return vals[8]
        return None

    def test_pheno_without_family_filters(self):
        url = "/api/v2/pheno_reports"
        data = {
            'phenoMeasure': 'ssc_commonly_used.head_circumference',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        self.assertIn('measure', response.data)
        self.assertEqual(
            'ssc_commonly_used.head_circumference', response.data['measure'])
        self.assertEqual(
            'ssc_commonly_used.head_circumference', response.data['formula'])

        data = response.data['data']
        self.assertEqual(310, self.pos_count('LGDs', data))
        self.assertEqual(2047, self.neg_count('LGDs', data))

    def test_family_pheno_filter_families_count(self):
        measures = preloaded.register.get_register().get('pheno_measures')
        families = measures.get_measure_families(
            'pheno_common.non_verbal_iq', 0, 40)
        self.assertEquals(224, len(families))

    def test_pheno_with_family_pheno_filter(self):
        url = "/api/v2/pheno_reports"
        data = {
            'phenoMeasure': 'ssc_commonly_used.head_circumference',
            'familyPhenoMeasure': 'pheno_common.non_verbal_iq',
            'familyPhenoMeasureMin': 0,
            'familyPhenoMeasureMax': 40,

        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        self.assertIn('measure', response.data)
        self.assertEqual(
            'ssc_commonly_used.head_circumference', response.data['measure'])
        self.assertEqual(
            'ssc_commonly_used.head_circumference', response.data['formula'])

        data = response.data['data']
        self.assertEqual(28, self.pos_count('LGDs', data))
        self.assertEqual(158, self.neg_count('LGDs', data))
