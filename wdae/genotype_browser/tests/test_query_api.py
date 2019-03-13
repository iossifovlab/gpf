'''
Created on Feb 6, 2017

@author: lubo
'''
import copy
import json

from rest_framework import status


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


URL = "/api/v3/genotype_browser/preview"


def test_missing_dataset(db, client):
    data = copy.deepcopy(EXAMPLE_REQUEST_SSC)
    del data['datasetId']

    response = client.post(URL, json.dumps(data), content_type='application/json')
    assert status.HTTP_400_BAD_REQUEST, response.status_code


def test_bad_dataset(db, client):
    data = copy.deepcopy(EXAMPLE_REQUEST_SSC)
    data['datasetId'] = 'ala bala portokala'

    response = client.post(URL, json.dumps(data), content_type='application/json')
    assert status.HTTP_400_BAD_REQUEST, response.status_code
