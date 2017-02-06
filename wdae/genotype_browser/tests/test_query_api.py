'''
Created on Feb 6, 2017

@author: lubo
'''
from rest_framework.test import APITestCase
from rest_framework import status
import copy


EXAMPLE_REQUEST = {
    "effectTypes": "Frame-shift,Nonsense,Splice-site",
    "families": "Advanced",
    "gender": "female,male",
    "presentInChild": "autism and unaffected,autism only",
    "presentInParent": "neither",
    "variantTypes": "CNV,del,ins,sub",
    "genes": "All",
    "familyRace": "All",
    "familyQuadTrio": "All",
    "familyPrbGender": "All",
    "familySibGender": "All",
    "familyStudyType": "All",
    "familyStudies": "All",
    "familyPhenoMeasureMin": 1.08,
    "familyPhenoMeasureMax": 40,
    "familyPhenoMeasure": "abc.subscale_ii_lethargy",
    "dataset": "SSC"
}


class Test(APITestCase):
    URL = "/api/v3/genotype_browser/preview"

    def test_query_preview(self):
        data = copy.deepcopy(EXAMPLE_REQUEST)

        response = self.client.post(
            self.URL, data, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_missing_dataset(self):
        data = copy.deepcopy(EXAMPLE_REQUEST)
        del data['dataset']

        response = self.client.post(
            self.URL, data, format='json')
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_bad_dataset(self):
        data = copy.deepcopy(EXAMPLE_REQUEST)
        data['dataset'] = 'ala bala portokala'

        response = self.client.post(
            self.URL, data, format='json')
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)
