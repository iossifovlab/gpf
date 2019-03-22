import pytest

import json

from rest_framework import status

pytestmark = pytest.mark.usefixtures("mock_studies_manager")

URL = "/api/v3/genotype_browser/preview"

FILTER_QUERY_CATEGORICAL = {
    "id": "Categorical",
    "measureType": "categorical",
    "role": "prb",
    "measure": "instrument1.categorical",
    "selection": {
        "selection": ["option2"]
    }
}

FILTER_QUERY_CONTINUOUS = {
    "id": "Continuous",
    "measureType": "continuous",
    "role": "prb",
    "measure": "instrument1.continuous",
    "selection": {
        "min": 3,
        "max": 4
    }
}

FILTER_QUERY_BOGUS = {
    "id": "some nonexistant measure",
    "measureType": "continuous",
    "role": "prb",
    "measure": "wrontinstrument.wrongmeasure",
    "selection": {
        "min": 3,
        "max": 4
    }
}

FILTER_QUERY_ORDINAL = {
    "id": "Ordinal",
    "measureType": "ordinal",
    "role": "prb",
    "measure": "instrument1.ordinal",
    "selection": {
        "min": 1,
        "max": 5
    }
}


def test_simple_query_passes(db, admin_client):
    data = {
        "datasetId": "quads_f1"
    }
    response = admin_client.post(
        URL, json.dumps(data), content_type="application/json")
    assert status.HTTP_200_OK == response.status_code


def test_simple_query(db, admin_client):
    data = {
        "datasetId": "quads_f1"
    }
    response = admin_client.post(
        URL, json.dumps(data), content_type="application/json")
    assert status.HTTP_200_OK == response.status_code
    res = response.data

    assert 4 == len(res["rows"])


@pytest.mark.parametrize("pheno_filters,variants_count", [
    ([FILTER_QUERY_CATEGORICAL], 2),
    ([FILTER_QUERY_CONTINUOUS], 2),
    ([FILTER_QUERY_CATEGORICAL, FILTER_QUERY_CONTINUOUS], 2),
])
def test_query_with_pheno_filters(db, admin_client, pheno_filters, variants_count):
    data = {
        "datasetId": "quads_f1",
        "phenoFilters": pheno_filters
    }
    response = admin_client.post(
        URL, json.dumps(data), content_type="application/json")
    assert status.HTTP_200_OK == response.status_code
    res = response.data

    assert variants_count == len(res["rows"])
