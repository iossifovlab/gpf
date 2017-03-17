'''
Created on Apr 28, 2016

@author: lubo
'''
import unittest
from rest_framework.test import APITestCase
from pheno_report import pheno_request, pheno_tool
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token


class Test(unittest.TestCase):

    def test_single_gene_sym_lgds_only(self):
        data = {
            'denovoStudies': 'ALL SSC',
            'phenoMeasure': 'ssc_commonly_used.head_circumference',
            'transmittedStudies': 'w1202s766e611',
            'presentInParent': "father only",
            'geneSyms': "POGZ",
            'effectTypeGroups': 'LGDs',

        }
        req = pheno_request.Request(data)
        tool = pheno_tool.PhenoTool(req)

        res = tool.calc()
        print(res)

        self.assertEquals(2, len(res))
        [male, female] = res
        self.assertEquals(male['effectType'], 'LGDs')
        self.assertEquals(female['effectType'], 'LGDs')


class TestViews(APITestCase):

    @classmethod
    def setUpClass(cls):
        super(TestViews, cls).setUpClass()

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
        super(TestViews, cls).tearDownClass()
        cls.user.delete()

    def setUp(self):
        super(TestViews, self).setUpClass()
        self.client.login(email='admin@example.com', password='secret')
        token = Token.objects.get(user__email='admin@example.com')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def tearDown(self):
        pass

    def test_single_gene_sym_lgds_only(self):
        url = "/api/v2/pheno_reports"
        data = {
            'denovoStudies': 'ALL SSC',
            'transmittedStudies': 'w1202s766e611',
            'presentInParent': "father only",
            'geneSyms': "POGZ",
            'phenoMeasure': 'ssc_commonly_used.head_circumference',
            'effectTypeGroups': 'LGDs'

        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        data = response.data['data']
        self.assertEquals(2, len(data))
        self.assertEquals('LGDs', data[0][0])
        self.assertEquals('LGDs', data[1][0])

    def test_single_gene_sym_lgds_and_missense(self):
        url = "/api/v2/pheno_reports"
        data = {
            'denovoStudies': 'ALL SSC',
            'transmittedStudies': 'w1202s766e611',
            'presentInParent': "father only",
            'geneSyms': "POGZ",
            'phenoMeasure': 'ssc_commonly_used.head_circumference',
            'effectTypeGroups': 'LGDs,missense'

        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(200, response.status_code)
        data = response.data['data']
        self.assertEquals(4, len(data))
        self.assertEquals('LGDs', data[0][0])
        self.assertEquals('LGDs', data[1][0])
        self.assertEquals('missense', data[2][0])
        self.assertEquals('missense', data[3][0])
