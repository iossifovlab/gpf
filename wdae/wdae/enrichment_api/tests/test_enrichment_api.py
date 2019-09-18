import pytest

import json


pytestmark = pytest.mark.usefixtures('mock_gpf_instance')


def test_enrichment_models(admin_client):
    response = admin_client.get('/api/v3/enrichment/models/f1_trio')

    assert response
    assert response.status_code == 200

    result = response.data
    assert result
    assert len(result) == 2

    assert len(result['background']) == 3
    background = result['background']
    background.sort(key=lambda x: x['name'])
    assert len(background[0]) == 2
    assert background[0]['name'] == 'codingLenBackgroundModel'
    assert background[0]['desc'] == 'Coding Len Background Model'
    assert len(background[1]) == 2
    assert background[1]['name'] == 'samochaBackgroundModel'
    assert background[1]['desc'] == 'Samocha Background Model'
    assert len(background[2]) == 2
    assert background[2]['name'] == 'synonymousBackgroundModel'
    assert background[2]['desc'] == 'Synonymous Background Model'

    assert len(result['counting']) == 2
    counting = result['counting']
    counting.sort(key=lambda x: x['name'])
    assert len(counting[0]) == 2
    assert counting[0]['name'] == 'enrichmentEventsCounting'
    assert counting[0]['desc'] == 'Enrichment Events Counting'
    assert len(counting[1]) == 2
    assert counting[1]['name'] == 'enrichmentGeneCounting'
    assert counting[1]['desc'] == 'Enrichment Gene Counting'


def test_enrichment_models_missing_study(admin_client):
    response = admin_client.get('/api/v3/enrichment/models/f1')

    assert response
    assert response.status_code == 200

    result = response.data
    assert result
    assert len(result) == 2
    assert len(result['background']) == 0
    assert len(result['counting']) == 0


def test_enrichment_test_missing_dataset_id(admin_client):
    url = '/api/v3/enrichment/test'
    query = {
        'enrichmentBackgroundModel': 'synonymousBackgroundModel',
        'enrichmentCountingModel': 'enrichmentGeneCounting',
        'geneSymbols': [
            'POGZ'
        ]
    }
    response = admin_client.post(
        url, json.dumps(query), content_type='application/json', format='json')

    assert response
    assert response.status_code == 400


def test_enrichment_test_missing_study(admin_client):
    url = '/api/v3/enrichment/test'
    query = {
        'datasetId': 'f1',
        'enrichmentBackgroundModel': 'synonymousBackgroundModel',
        'enrichmentCountingModel': 'enrichmentGeneCounting',
        'geneSymbols': [
            'POGZ'
        ]
    }
    response = admin_client.post(
        url, json.dumps(query), content_type='application/json', format='json')

    assert response
    assert response.status_code == 404


def test_enrichment_test_missing_gene_symbols(admin_client):
    url = '/api/v3/enrichment/test'
    query = {
        'datasetId': 'f1_trio',
        'enrichmentBackgroundModel': 'synonymousBackgroundModel',
        'enrichmentCountingModel': 'enrichmentGeneCounting',
    }
    response = admin_client.post(
        url, json.dumps(query), content_type='application/json', format='json')

    assert response
    assert response.status_code == 400


def test_enrichment_test_gene_symbols(admin_client):
    url = '/api/v3/enrichment/test'
    query = {
        'datasetId': 'f1_trio',
        'enrichmentBackgroundModel': 'codingLenBackgroundModel',
        'enrichmentCountingModel': 'enrichmentGeneCounting',
        'geneSymbols': [
            'SAMD11',
            'PLEKHN1',
            'POGZ'
        ]
    }
    response = admin_client.post(
        url, json.dumps(query), content_type='application/json', format='json')

    assert response
    assert response.status_code == 200

    result = response.data
    assert len(result) == 2

    assert result['desc'][:14] == 'Gene Symbols: '
    assert result['desc'][:14] == 'Gene Symbols: '
    assert result['desc'][-4:] == ' (3)'
    assert sorted(result['desc'][14:-4].split(',')) == \
        sorted(['SAMD11', 'PLEKHN1', 'POGZ'])

    assert len(result['result']) == 2
    assert len(result['result'][0]) == 6
    assert result['result'][0]['selector'] == 'autism'
    assert result['result'][0]['peopleGroupId'] == 'phenotype'
    assert len(result['result'][0]['childrenStats']) == 2
    assert result['result'][0]['childrenStats']['M'] == 1
    assert result['result'][0]['childrenStats']['F'] == 1
    assert result['result'][0]['LGDs']['all']['count'] == 0
    assert result['result'][0]['LGDs']['rec']['count'] == 0
    assert result['result'][0]['LGDs']['male']['count'] == 0
    assert result['result'][0]['LGDs']['female']['count'] == 0
    assert result['result'][0]['missense']['all']['count'] == 1
    assert result['result'][0]['missense']['rec']['count'] == 1
    assert result['result'][0]['missense']['male']['count'] == 1
    assert result['result'][0]['missense']['female']['count'] == 1
    assert result['result'][0]['synonymous']['all']['count'] == 1
    assert result['result'][0]['synonymous']['rec']['count'] == 1
    assert result['result'][0]['synonymous']['male']['count'] == 1
    assert result['result'][0]['synonymous']['female']['count'] == 1

    assert len(result['result'][1]) == 6
    assert result['result'][1]['selector'] == 'unaffected'
    assert result['result'][1]['peopleGroupId'] == 'phenotype'
    assert len(result['result'][1]['childrenStats']) == 1
    assert result['result'][1]['childrenStats']['F'] == 1
    assert result['result'][1]['LGDs']['all']['count'] == 0
    assert result['result'][1]['LGDs']['rec']['count'] == 0
    assert result['result'][1]['LGDs']['male']['count'] == 0
    assert result['result'][1]['LGDs']['female']['count'] == 0
    assert result['result'][1]['missense']['all']['count'] == 0
    assert result['result'][1]['missense']['rec']['count'] == 0
    assert result['result'][1]['missense']['male']['count'] == 0
    assert result['result'][1]['missense']['female']['count'] == 0
    assert result['result'][1]['synonymous']['all']['count'] == 1
    assert result['result'][1]['synonymous']['rec']['count'] == 0
    assert result['result'][1]['synonymous']['male']['count'] == 0
    assert result['result'][1]['synonymous']['female']['count'] == 1


def test_enrichment_test_gene_set(admin_client):
    url = '/api/v3/enrichment/test'
    query = {
        'datasetId': 'f1_trio',
        'enrichmentBackgroundModel': 'codingLenBackgroundModel',
        'enrichmentCountingModel': 'enrichmentGeneCounting',
        'geneSet': {
            'geneSetsCollection': 'denovo',
            'geneSet': 'Missense',
            'geneSetsTypes': {
                'f1_trio': {'phenotype': ['autism']}
            }
        }
    }
    response = admin_client.post(
        url, json.dumps(query), content_type='application/json', format='json')

    assert response
    assert response.status_code == 200

    result = response.data
    assert len(result) == 2

    assert result['desc'] == \
        'Gene Set: Missense (f1_trio:phenotype:autism) (1)'
