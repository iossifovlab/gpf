'''
Created on Apr 13, 2017

@author: lubo
'''
import copy

from rest_framework import status

from users_api.tests.base_tests import BaseAuthenticatedUserTest


EXAMPLE_REQUEST_SSC = {
    "effectTypes": ["Frame-shift", "Nonsense", "Splice-site"],
    "gender": ["female", "male"],
    "presentInChild": [
        "affected and unaffected",
        "affected only",
    ],
    "presentInParent": [
        "neither",
    ],
    "variantTypes": [
        "CNV", "del", "ins", "sub",
    ],
    "genes": "All",
    "datasetId": "SSC",
    "peopleGroup": {
        "id": "phenotype",
        "checkedValues": ["autism", "unaffected"]
    }
}


class Test(BaseAuthenticatedUserTest):

    URL = "/api/v3/family_counters/counters"

    def test_query_counter_all(self):

        data = copy.deepcopy(EXAMPLE_REQUEST_SSC)

        response = self.client.post(
            self.URL, data, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        res = response.data
        self.assertEquals(2206, res[1]['count']['all'])
        self.assertEquals(1171, res[1]['count']['F'])
        self.assertEquals(1035, res[1]['count']['M'])

    def test_query_counter_with_single_family_id(self):

        data = copy.deepcopy(EXAMPLE_REQUEST_SSC)
        data['familyIds'] = ['11110']

        response = self.client.post(
            self.URL, data, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        res = response.data

        self.assertEquals(1, res[1]['count']['all'])
        self.assertEquals(0, res[1]['count']['F'])
        self.assertEquals(1, res[1]['count']['M'])

        self.assertEquals(1, res[0]['count']['all'])
        self.assertEquals(0, res[0]['count']['F'])
        self.assertEquals(1, res[0]['count']['M'])

    def test_query_counter_with_nonverbal_iq(self):

        data = copy.deepcopy(EXAMPLE_REQUEST_SSC)
        data['phenoFilters'] = [
            {
                'measureType': 'continuous',
                'measure': 'ssc_core_descriptive.ssc_diagnosis_nonverbal_iq',
                'role': 'prb',
                'mmin': 80,
                'mmax': 80.5
            }
        ]

        response = self.client.post(
            self.URL, data, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        res = response.data

        self.assertEquals(25, res[1]['count']['all'])
        self.assertEquals(10, res[1]['count']['F'])
        self.assertEquals(15, res[1]['count']['M'])

        self.assertEquals(29, res[0]['count']['all'])
        self.assertEquals(3, res[0]['count']['F'])
        self.assertEquals(26, res[0]['count']['M'])

    def test_query_counter_with_nonverbal_iq_and_race(self):

        data = copy.deepcopy(EXAMPLE_REQUEST_SSC)
        data['phenoFilters'] = [
            {
                'measureType': 'continuous',
                'measure': 'ssc_core_descriptive.ssc_diagnosis_nonverbal_iq',
                'role': 'prb',
                'mmin': 80,
                'mmax': 80.5,
            },
            {
                'measureType': 'categorical',
                'measure': 'pheno_common.race',
                'role': 'dad',
                'selection': ['african-amer'],
            },
            {
                'measureType': 'categorical',
                'measure': 'pheno_common.race',
                'role': 'mom',
                'selection': ['african-amer'],
            },
        ]

        response = self.client.post(
            self.URL, data, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        res = response.data

        self.assertEquals(2, res[1]['count']['all'])
        self.assertEquals(2, res[1]['count']['F'])
        self.assertEquals(0, res[1]['count']['M'])

        self.assertEquals(2, res[0]['count']['all'])
        self.assertEquals(0, res[0]['count']['F'])
        self.assertEquals(2, res[0]['count']['M'])

    def test_query_counter_with_single_wrong_family_id(self):

        data = copy.deepcopy(EXAMPLE_REQUEST_SSC)
        data['familyIds'] = ['aaa']

        response = self.client.post(
            self.URL, data, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        res = response.data

        self.assertEquals(0, res[0]['count']['all'])
        self.assertEquals(0, res[0]['count']['F'])
        self.assertEquals(0, res[0]['count']['M'])

        self.assertEquals(0, res[1]['count']['all'])
        self.assertEquals(0, res[1]['count']['F'])
        self.assertEquals(0, res[1]['count']['M'])

    def test_query_counter_with_bapq_average(self):
        query = {
            "datasetId": "SSC",
            "presentInChild": [
                "affected only",
                "affected and unaffected"
            ],
            "presentInParent": {
                "presentInParent": [
                    "neither"
                ],
                "rarity": {
                    "ultraRare": True,
                    "minFreq": None,
                    "maxFreq": None
                }
            },
            "gender": [
                "female",
                "male"
            ],
            "variantTypes": [
                "sub",
                "ins",
                "del",
                "CNV"
            ],
            "effectTypes": [
                "Nonsense",
                "Frame-shift",
                "Splice-site"
            ],
            "phenoFilters": [
                {
                    "id": "Proband Pheno Measure",
                    "measureType": "continuous",
                    "role": "prb",
                    "measure": "bapq.average",
                    "domainMin": 1,
                    "domainMax": 4.97,
                    "mmin": 1,
                    "mmax": 3.0816666666666666
                }
            ]
        }

        response = self.client.post(
            self.URL, query, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        res = response.data

        self.assertEquals(0, res[0]['count']['all'])
        self.assertEquals(0, res[0]['count']['F'])
        self.assertEquals(0, res[0]['count']['M'])

        self.assertEquals(0, res[1]['count']['all'])
        self.assertEquals(0, res[1]['count']['F'])
        self.assertEquals(0, res[1]['count']['M'])
