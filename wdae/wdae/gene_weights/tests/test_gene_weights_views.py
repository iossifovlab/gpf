import pytest

import json

pytestmark = pytest.mark.usefixtures('wdae_gpf_instance', 'calc_gene_sets')


def test_gene_weights_list_view(user_client):
    url = '/api/v3/gene_weights'
    response = user_client.get(url)
    assert response.status_code == 200

    data = response.data
    print([d['weight'] for d in data])
    assert len(data) == 5

    for w in response.data:
        assert 'desc' in w
        assert 'weight' in w
        assert 'bars' in w
        assert 'bins' in w


def test_gene_weights_get_genes_view(user_client):
    url = '/api/v3/gene_weights/genes'
    data = {
        'weight': 'LGD_rank',
        'min': 1.5,
        'max': 5.0,
    }
    response = user_client.post(
        url, json.dumps(data), content_type='application/json', format='json')
    assert response.status_code == 200
    print(response.data)

    assert len(response.data) == 3
