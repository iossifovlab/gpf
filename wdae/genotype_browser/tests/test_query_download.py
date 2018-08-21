'''
Created on Jul 11, 2017

@author: lubo
'''
from users_api.tests.base_tests import BaseAuthenticatedUserTest
import copy
from rest_framework import status
import urllib
import json
EXAMPLE_REQUEST_SVIP = {
    "effectTypes": ["Frame-shift", "Nonsense", "Splice-site"],
    "gender": ["female", "male"],
    "presentInParent": [
        "neither",
    ],
    "variantTypes": [
        "CNV", "del", "ins", "sub",
    ],
    "genes": "All",
    "datasetId": "SVIP",
    "pedigreeSelector": {
        "id": "16pstatus",
        "checkedValues": [
            "deletion",
            "duplication",
            "triplication",
            "negative"]
    }
}


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
    "pedigreeSelector": {
        "id": "phenotype",
        "checkedValues": ["autism", "unaffected"]
    }
}

EXAMPLE_REQUEST_SD = {
    "datasetId": "SD",
    "effectTypes": ["Frame-shift", "Nonsense", "Splice-site"],
    "gender": ["female", "male"],
    "variantTypes": [
        "del", "ins", "sub",
    ],
    "geneSet": {
        "geneSetsCollection": "main",
        "geneSet": "autism candidates from Iossifov PNAS 2015",
        "geneSetsTypes": []
    },
    "pedigreeSelector": {
        "id": "phenotype",
        "checkedValues": [
            "autism", "unaffected", "congenital_heart_disease",
            "epilepsy", "schizophrenia",
            "intellectual_disability"]
    }
}


EXAMPLE_REQUEST_DENOVO_DB = {
    "datasetId": "denovo_db",
    "genomicScores": [],
    "pedigreeSelector": {
        "id": "phenotype",
        "checkedValues": [
            "acromelic_frontonasal_dysostosis",
            "amyotrophic_lateral_sclerosis",
            "anophthalmia_microphthalmia",
            "autism",
            "bipolar_type1",
            "cantu_syndrome",
            "congenital_diaphragmatic_hernia",
            "congenital_heart_disease",
            "developmental_disorder",
            "early_onset_alzheimer",
            "early_onset_parkinson",
            "epilepsy",
            "intellectual_disability",
            "neural_tube_defects",
            "schizophrenia",
            "sporadic_infantile_spasm_syndrome",
            "unaffected"
        ]
    },
    "gender": [
        "female",
        "male",
        "unspecified"
    ],
    "variantTypes": [
        "sub",
        "ins",
        "del"
    ],
    "effectTypes": [
        "Nonsense",
        "Frame-shift",
        "Splice-site"
    ]
}


def count_iterable(iterable):
    for num, _it in enumerate(iterable):
        pass
    return num + 1


def collect(iterable):
    res = []
    header = next(iterable)
    for v in iterable:
        res.append(v)
    return header, res


class Test(BaseAuthenticatedUserTest):

    URL = "/api/v3/genotype_browser/download"

    def test_query_download_urlencoded(self):
        data = copy.deepcopy(EXAMPLE_REQUEST_SVIP)
        query = urllib.urlencode({"queryData": json.dumps(data)})

        response = self.client.post(
            self.URL, query, content_type='application/x-www-form-urlencoded')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        self.assertEqual(64 + 1, count_iterable(response.streaming_content))

    def test_query_download_json(self):
        data = copy.deepcopy(EXAMPLE_REQUEST_SVIP)
        query = {"queryData": json.dumps(data)}

        response = self.client.post(
            self.URL, query, format="json")
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        self.assertEqual(64 + 1, count_iterable(response.streaming_content))


class TestDownloadStudyPhenotype(BaseAuthenticatedUserTest):

    URL = "/api/v3/genotype_browser/download"

    def test_query_download_ssc(self):
        data = copy.deepcopy(EXAMPLE_REQUEST_SSC)
        query = urllib.urlencode({"queryData": json.dumps(data)})

        response = self.client.post(
            self.URL, query, content_type='application/x-www-form-urlencoded')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        header, res = collect(response.streaming_content)
        assert header is not None
        assert res is not None

        assert 422 == len(res)
        for v in res:
            variant = {k: v for k, v in zip(header.split('\t'), v.split('\t'))}

            study_phenotype = variant['phenotype']
            assert study_phenotype == 'autism'

    def test_query_download_svip(self):
        data = copy.deepcopy(EXAMPLE_REQUEST_SVIP)
        query = urllib.urlencode({"queryData": json.dumps(data)})

        response = self.client.post(
            self.URL, query, content_type='application/x-www-form-urlencoded')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        header, res = collect(response.streaming_content)
        assert header is not None
        assert res is not None

        assert 64 == len(res)

        for v in res:
            variant = {k: v for k, v in zip(header.split('\t'), v.split('\t'))}

            study_phenotype = variant['phenotype']
            assert study_phenotype == 'ASD and other neurodevelopmental'\
                ' disorders'

    def test_query_download_sd_autism(self):
        data = copy.deepcopy(EXAMPLE_REQUEST_SD)
        data['pedigreeSelector']['checkedValues'] = ['autism']
        query = urllib.urlencode({"queryData": json.dumps(data)})

        response = self.client.post(
            self.URL, query, content_type='application/x-www-form-urlencoded')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        header, res = collect(response.streaming_content)
        assert header is not None
        assert res is not None

        assert 622 == len(res)

        for v in res:
            variant = {k: v for k, v in zip(header.split('\t'), v.split('\t'))}

            study_phenotype = variant['phenotype']
            assert study_phenotype == 'autism'

    def test_query_download_sd_unaffected(self):
        data = copy.deepcopy(EXAMPLE_REQUEST_SD)
        data['pedigreeSelector']['checkedValues'] = ['unaffected']
        query = urllib.urlencode({"queryData": json.dumps(data)})

        response = self.client.post(
            self.URL, query, content_type='application/x-www-form-urlencoded')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        header, res = collect(response.streaming_content)
        assert header is not None
        assert res is not None

        assert 233 == len(res)

        for v in res:
            variant = {k: v for k, v in zip(header.split('\t'), v.split('\t'))}

            study_phenotype = variant['phenotype']
            assert study_phenotype in [
                "autism", "unaffected", "congenital_heart_disease",
                "epilepsy", "schizophrenia",
                "intellectual_disability"
            ]

    def test_query_download_denovo_db_autism(self):
        data = copy.deepcopy(EXAMPLE_REQUEST_DENOVO_DB)
        data['pedigreeSelector']['checkedValues'] = ['autism']
        query = urllib.urlencode({"queryData": json.dumps(data)})

        response = self.client.post(
            self.URL, query, content_type='application/x-www-form-urlencoded')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        header, res = collect(response.streaming_content)
        assert header is not None
        assert res is not None

        assert 94 == len(res)

        for v in res:
            variant = {k: v for k, v in zip(header.split('\t'), v.split('\t'))}
            study_phenotype = variant['Study Phenotype']
            assert study_phenotype == 'autism'

    def test_query_download_denovo_db_unaffected(self):
        data = copy.deepcopy(EXAMPLE_REQUEST_DENOVO_DB)
        data['pedigreeSelector']['checkedValues'] = ['unaffected']
        query = urllib.urlencode({"queryData": json.dumps(data)})

        response = self.client.post(
            self.URL, query, content_type='application/x-www-form-urlencoded')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        header, res = collect(response.streaming_content)
        assert header is not None
        assert res is not None

        assert 20 == len(res)

        for v in res:
            variant = {k: v for k, v in zip(header.split('\t'), v.split('\t'))}

            study_phenotype = variant['Study Phenotype']
            assert study_phenotype in [
                "acromelic_frontonasal_dysostosis",
                "amyotrophic_lateral_sclerosis",
                "anophthalmia_microphthalmia",
                "autism",
                "bipolar_type1",
                "cantu_syndrome",
                "congenital_diaphragmatic_hernia",
                "congenital_heart_disease",
                "developmental_disorder",
                "early_onset_alzheimer",
                "early_onset_parkinson",
                "epilepsy",
                "intellectual_disability",
                "neural_tube_defects",
                "schizophrenia",
                "sporadic_infantile_spasm_syndrome",
                "unaffected"
            ]
