'''
Created on Jul 23, 2015

@author: lubo
'''
from rest_framework import status
from users_api.tests.base_tests import BaseAuthenticatedUserTest
import pytest


@pytest.mark.skip(reason="no way of currently testing this")
class Test(BaseAuthenticatedUserTest):

    def test_query_by_region(self):
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
        self.assertEqual('2', response.data['count'])
