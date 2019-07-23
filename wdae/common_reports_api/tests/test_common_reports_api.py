import pytest

pytestmark = pytest.mark.usefixtures(
    'mock_studies_manager', 'use_common_reports')


def test_studies_summaries_columns(user_client):
    url = '/api/v3/common_reports'
    response = user_client.get(url)

    assert response
    assert response.status_code == 200

    data = response.data
    assert data

    assert len(data) == 2
    assert len(data['columns']) == 10
    assert data['columns'] == [
        'study name', 'phenotype', 'study type', 'study year', 'PubMed',
        'families', 'number of probands', 'number of siblings', 'denovo',
        'transmitted'
    ]


def test_studies_summaries(user_client):
    url = '/api/v3/common_reports'
    response = user_client.get(url)

    assert response
    assert response.status_code == 200

    data = response.data
    assert data

    assert len(data) == 2
    assert len(data['summaries']) == 4

    assert 'study name' in data['summaries'][0]
    assert 'description' in data['summaries'][0]
    assert 'phenotype' in data['summaries'][0]
    assert 'study type' in data['summaries'][0]
    assert 'study year' in data['summaries'][0]
    assert 'PubMed' in data['summaries'][0]
    assert 'families' in data['summaries'][0]
    assert 'number of probands' in data['summaries'][0]
    assert 'number of siblings' in data['summaries'][0]
    assert 'denovo' in data['summaries'][0]
    assert 'transmitted' in data['summaries'][0]
    assert 'id' in data['summaries'][0]

    assert sorted([
        summary['study name'] for summary in data['summaries']
    ]) == sorted([
        'Study1', 'Study3', 'Study4', 'Dataset1'
    ])

    assert sorted([
        summary['id'] for summary in data['summaries']
    ]) == sorted([
        'Study1', 'Study3', 'study4', 'Dataset1'
    ])
