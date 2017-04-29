'''
Created on Jul 23, 2015

@author: lubo
'''
from rest_framework import status
from users.tests.base_tests import BaseAuthenticatedUserTest


class Test(BaseAuthenticatedUserTest):

    def test_authenticated(self):
        region = "1:151377900-151378500"
        data = {
            "effectTypes": "Nonsense,Frame-shift,Splice-site",
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "None",
            "presentInChild": "autism only",
            "gender": "male,female",
            "geneRegion": region,
        }

        url = '/api/ssc_query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated(self):
        region = "1:151377900-151378500"
        data = {
            "effectTypes": "Nonsense,Frame-shift,Splice-site",
            "denovoStudies": "ALL SSC",
            "transmittedStudies": "None",
            "presentInChild": "autism only",
            "gender": "male,female",
            "geneRegion": region,
        }

        self.client.logout()

        url = '/api/ssc_query_variants_preview'

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
