'''
Created on Jan 4, 2016

@author: lubo
'''
import unittest
from rest_framework.test import APITestCase
from rest_framework import status
import json
from query_variants import prepare_denovo_filters, get_denovo_variants
from DAE import vDB
from Variant import normalRefCopyNumber


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
        self.assertEqual(2, m[0][-1])
        self.assertEqual(1, m[1][-1])
        self.assertEqual(2, m[2][-1])
        self.assertEqual(1, m[3][-1])

    def test_all_pedigree(self):
        data = {
            'denovoStudies': 'ALL WHOLE EXOME',
            'geneSyms': None,
            'gender': 'female,male',
            'genes': 'All',
            'effectTypes': "frame-shift,intergenic,intron,missense,non-coding,"
            "no-frame-shift,nonsense,splice-site,synonymous,noEnd,noStart,"
            "3'UTR,3'UTR-intron,5'UTR,5'UTR-intron",
            'phenoType': 'autism,congenital heart disease,'
            'epilepsy,intelectual disability,schizophrenia,unaffected',
            'variantTypes': 'del,ins,sub',
            'transmittedStudies': None,
            'studyType': 'TG,WE'}

        filters = prepare_denovo_filters(data)
        study_names = vDB.get_study_names()
        studies = []
        for sn in study_names:
            st = vDB.get_study(sn)
            if st.has_denovo:
                studies.append((st, None))
                print("adding study: {}".format(sn))

        vs = get_denovo_variants(studies, family_filters=None, **filters)
        for v in vs:
            location = v.location
            bs = v.bestSt
            for (c, m) in enumerate(v.memberInOrder):
                gender = m.gender
                normal = normalRefCopyNumber(location, gender)
                # print("variantCount: {}, {}, {}".format(
                # location, gender, normalRefCN))
                ref = bs[0, c]
                # print("count: {}".format(count))
                if bs.shape[0] == 2:
                    alles = bs[1, c]
                    if alles != 0:
                        if ref == normal:
                            print("------------------------------------------")
                            print("Study: {}".format(v.studyName))
                            print(v.atts)
                            print("location: {}, gender: {}, c: {}, normal: {}"
                                  .format(location, gender, c, normal))
                            print("bs: {}".format(bs))
                            print("------------------------------------------")

if __name__ == "__main__":
    unittest.main()
