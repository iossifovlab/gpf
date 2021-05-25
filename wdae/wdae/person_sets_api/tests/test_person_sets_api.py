import pytest
from rest_framework import status

pytestmark = pytest.mark.usefixtures(
    "wdae_gpf_instance", "dae_calc_gene_sets")


def test_list_collections_view(admin_client):
    url = "/api/v3/person_sets/Study1/all"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data[0] == {
        'id': 'phenotype',
        'name': 'Phenotype',
        'person_sets': [
            {
                'color': '#e35252',
                'id': 'phenotype1',
                'name': 'phenotype 1',
                'person_ids': [
                    'ch1',
                    'ch3',
                    'mom4',
                    'ch4',
                    'mom5',
                    'ch5',
                    'ch6',
                    'mom7',
                    'mom8',
                    'ch8',
                    'ch9',
                    'ch9.1',
                    'ch9.2',
                    'ch10',
                    'ch10.1',
                    'ch10.2'
                ],
                'values': {'phenotype1'}
            },
            {
                'color': '#b8008a',
                'id': 'phenotype2',
                'name': 'phenotype 2',
                'person_ids': [
                    'ch4.1',
                    'ch5.1',
                    'ch7',
                    'ch8.1'
                ],
                'values': {'phenotype2'}
            },
            {
                'color': '#ffffff',
                'id': 'unaffected',
                'name': 'unaffected',
                'person_ids': [
                    'mom1',
                    'dad1',
                    'mom3',
                    'dad3',
                    'mom6',
                    'dad6',
                    'mom11',
                    'dad11',
                    'ch11'
                ],
                'values': {'unaffected'}
            },
            {
                'color': '#aaaaaa',
                'id': 'unknown',
                'name': 'unknown',
                'person_ids': [
                    'dad4',
                    'dad5',
                    'dad7',
                    'dad8'
                ],
                'values': {'DEFAULT'}
            }
        ]
    }


def test_collection_configs_view(admin_client):
    url = "/api/v3/person_sets/Study1/configs"
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data == {
        'phenotype': {
            'domain': [
                {
                    'color': '#e35252',
                    'id': 'phenotype1',
                    'name': 'phenotype 1',
                    'values': {'phenotype1'}
                },
                {
                    'color': '#b8008a',
                    'id': 'phenotype2',
                    'name': 'phenotype 2',
                    'values': {'phenotype2'}
                },
                {
                    'color': '#ffffff',
                    'id': 'unaffected',
                    'name': 'unaffected',
                    'values': {'unaffected'}
                },
                {
                    'color': '#aaaaaa',
                    'id': 'unknown',
                    'name': 'unknown',
                    'values': {'DEFAULT'}
                }
            ],
            'id': 'phenotype',
            'name': 'Phenotype'
        },
    }
