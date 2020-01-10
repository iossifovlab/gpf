import pytest

import json

from rest_framework import status

pytestmark = pytest.mark.usefixtures('wdae_gpf_instance', 'calc_gene_sets')

PREVIEW_URL = '/api/v3/genotype_browser/preview'
PREVIEW_VARIANTS_URL = '/api/v3/genotype_browser/preview/variants'


def test_query_preview_have_pheno_columns(db, admin_client):
    data = {
        'datasetId': 'quads_f1'
    }
    response = admin_client.post(
        PREVIEW_URL, json.dumps(data), content_type='application/json'
    )
    assert status.HTTP_200_OK == response.status_code
    res = response.data

    assert 'continuous.Continuous' in res['cols']
    assert 'categorical.Categorical' in res['cols']
    assert 'ordinal.Ordinal' in res['cols']
    assert 'raw.Raw' in res['cols']


def test_query_preview_have_pheno_column_values(db, admin_client):
    data = {
        'datasetId': 'quads_f1'
    }
    response = admin_client.post(
        PREVIEW_VARIANTS_URL, json.dumps(data), content_type='application/json'
    )
    assert status.HTTP_200_OK == response.status_code
    res = response.streaming_content
    res = json.loads(''.join(map(lambda x: x.decode('utf-8'), res)))

    assert len(res) == 3

    for row in enumerate(res):
        for value in row[-4:]:
            assert value is not None
