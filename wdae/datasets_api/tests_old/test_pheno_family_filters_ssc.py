'''
Created on Mar 25, 2017

@author: lubo
'''
from rest_framework import status
from users_api.tests.base_tests import BaseAuthenticatedUserTest


class Test(BaseAuthenticatedUserTest):

    def test_pheno_family_filters(self):
        url = '/api/v3/genotype_browser/preview'
        data = {
            'effectTypes': ['Frame-shift', 'Nonsense', 'Splice-site'],
            "gender": ["female", "male"],
            "presentInChild": [
                "affected and unaffected",
                "affected only",
            ],
            "presentInParent": [
                "neither"
            ],
            "variantTypes": [
                "CNV", "del", "ins", "sub",
            ],
            "datasetId": "SSC",
            "pedigreeSelector": {
                'id': "phenotype",
                "checkedValues": ["autism", "unaffected"]
            },
            "phenoFilters": [
                {
                    'measureType': 'categorical',
                    'measure': 'pheno_common.race',
                    'role': 'prb',
                    'selection': ['native-hawaiian', 'white'],
                },
                {
                    'measureType': 'continuous',
                    'measure':
                    'ssc_core_descriptive.ssc_diagnosis_nonverbal_iq',
                    'role': 'prb',
                    'mmin': 80,
                    'mmax': 80.5
                }
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertEquals('5', data['count'])

    def test_pheno_family_filters_by_study(self):
        url = '/api/v3/genotype_browser/preview'
        data = {
            'effectTypes': ['Frame-shift', 'Nonsense', 'Splice-site'],
            "gender": ["female", "male"],
            "presentInChild": [
                "affected and unaffected",
                "affected only",
            ],
            "presentInParent": [
                "neither"
            ],
            "variantTypes": [
                "CNV", "del", "ins", "sub",
            ],
            "datasetId": "SSC",
            "phenoFilters": [
                {
                    "id": "Study",
                    "measureType": "studies",
                    "role": "study",
                    "measure": "studyFilter",
                    "selection": ["LevyCNV2011"]
                }
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        # FIXME: changed after rennotation
        # self.assertEquals('121', data['count'])
        self.assertEquals('122', data['count'])

    def test_pheno_family_filters_by_study_type(self):
        url = '/api/v3/genotype_browser/preview'
        data = {
            'effectTypes': ['Frame-shift', 'Nonsense', 'Splice-site'],
            "gender": ["female", "male"],
            "presentInChild": [
                "affected and unaffected",
                "affected only",
            ],
            "presentInParent": [
                "neither"
            ],
            "variantTypes": [
                "CNV", "del", "ins", "sub",
            ],
            "datasetId": "SSC",
            "phenoFilters": [
                {
                    "id": "Study Type",
                    "measureType": "studies",
                    "role": "study",
                    "measure": "studyTypeFilter",
                    "selection": ["TG"]
                }
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        # FIXME: changed after rennotation
        # self.assertEquals('411', data['count'])
        self.assertEquals('415', data['count'])
