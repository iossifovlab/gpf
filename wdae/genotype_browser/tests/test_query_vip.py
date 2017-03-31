'''
Created on Feb 6, 2017

@author: lubo
'''
from rest_framework.test import APITestCase
from rest_framework import status
import copy
from django.contrib.auth import get_user_model


EXAMPLE_REQUEST_VIP = {
    "effectTypes": ["Frame-shift", "Nonsense", "Splice-site"],
    "gender": ["female", "male"],
    "presentInChild": [
        "affected and unaffected",
        "affected only",
        "unaffected only",
        "neither"
    ],
    "presentInParent": [
        "neither",
    ],
    "variantTypes": [
        "CNV", "del", "ins", "sub",
    ],
    "genes": "All",
    "datasetId": "VIP",
    "pedigreeSelector": {
        "id": "16pstatus",
        "checkedValues": ["deletion", "duplication"]
    }
}


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

    URL = "/api/v3/genotype_browser/preview"

    def test_query_preview(self):
        self.client.login(
            email='admin@example.com', password='secret')

        data = copy.deepcopy(EXAMPLE_REQUEST_VIP)

        response = self.client.post(
            self.URL, data, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        res = response.data

        self.assertIn('cols', res)
        self.assertIn('rows', res)
        self.assertIn('count', res)
        self.assertIn('legend', res)

        print(res['legend'])
        print(res['count'])
        self.assertEquals(5, len(res['legend']))
        self.assertEquals(62, int(res['count']))
        self.assertEquals(62, len(res['rows']))

        print(res['rows'])
