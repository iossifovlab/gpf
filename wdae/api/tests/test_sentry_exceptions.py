'''
Created on Apr 5, 2016

@author: lubo
'''
from rest_framework import status
from rest_framework.test import APITestCase


class Tests(APITestCase):

    @classmethod
    def setUpClass(cls):
        super(Tests, cls).setUpClass()
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
        super(Tests, cls).tearDownClass()
        cls.user.delete()

    def setUp(self):
        from rest_framework.authtoken.models import Token

        APITestCase.setUp(self)

        self.client.login(email='admin@example.com', password='secret')
        token = Token.objects.get(user__email='admin@example.com')
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_sentry_ssc_download_exception_request(self):
        data = {
            'denovoStudies': 'ALL SSC',
            'effectTypes': 'Missense',
            'families': 'Advanced',
            'familyIds': '',
            'familyPhenoMeasure': '',
            'familyPhenoMeasureMax': '',
            'familyPhenoMeasureMin': '',
            'familyPrbGender': 'All',
            'familyQuadTrio': 'Quad',
            'familyRace': 'white',
            'familySibGender': 'All',
            'familyVerbalIqHi': '',
            'familyVerbalIqLo': '',
            'gender': 'female,male',
            'gene_set_phenotype': 'autism',
            'geneRegion': '',
            'genes': 'Gene Sets',
            'geneSet': 'denovo',
            'geneSyms': '',
            'geneTerm': 'LGDs.Recurrent',
            'geneTermFilter': '',
            'geneWeight': '',
            'geneWeightMax': '',
            'geneWeightMin': '',
            'popFrequencyMax': '',
            'popFrequencyMin': '',
            'presentInChild': 'autism and unaffected,autism only',
            'presentInParent': 'mother only,father only,mother and father',
            'rarity': 'ultraRare',
            'variantTypes': 'CNV,del,ins,sub',
        }
        url = '/api/ssc_query_variants'
        response = self.client.post(url, data, format='json')
        self.assertEquals(status.HTTP_200_OK, response.status_code)

        response = self.client.post(
            url, data)
        self.assertEquals(status.HTTP_200_OK, response.status_code)

    def test_gene_list_exception(self):
        url = '/api/gene_set_list2?desc=true&filter=&gene_set=main&key=true&page_count=200'  # @IgnorePep8
        response = self.client.get(url)
        self.assertEquals(status.HTTP_200_OK, response.status_code)
