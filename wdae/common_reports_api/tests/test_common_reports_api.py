import pytest

from rest_framework import status

pytestmark = pytest.mark.usefixtures(
    'mock_studies_manager', 'use_common_reports')


def test_studies_summaries_columns(user_client):
    url = '/api/v3/common_reports'
    response = user_client.get(url)

    assert response
    assert response.status_code == status.HTTP_200_OK

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
    assert response.status_code == status.HTTP_200_OK

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


def test_variant_reports(admin_client):
    url = '/api/v3/common_reports/studies/study4'
    response = admin_client.get(url)

    assert response
    assert response.status_code == status.HTTP_200_OK

    data = response.data
    assert data

    assert data['is_downloadable'] is True


def test_variant_reports_no_permissions(user_client):
    url = '/api/v3/common_reports/studies/study4'
    response = user_client.get(url)

    assert response
    assert response.status_code == status.HTTP_200_OK

    data = response.data
    assert data

    assert data['is_downloadable'] is False


def test_variant_reports_not_found(user_client):
    url = '/api/v3/common_reports/studies/Study4'
    response = user_client.get(url)

    assert response
    assert response.data['error'] == 'Common report Study4 not found'
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_families_data_download(admin_client):
    url = '/api/v3/common_reports/families_data/Study1'
    response = admin_client.get(url)

    assert response
    assert response.status_code == status.HTTP_200_OK

    streaming_content = list(response.streaming_content)
    assert streaming_content

    assert len(streaming_content) == 31

    header = streaming_content[0].decode('utf8')
    assert header[-1] == '\n'
    header = header[:-1].split('\t')
    assert len(header) == 8

    assert header == [
        'familyId', 'personId', 'dadId', 'momId', 'gender', 'status', 'role',
        'study'
    ]

    first_person = streaming_content[1].decode('utf8')
    assert first_person[-1] == '\n'
    first_person = first_person[:-1].split('\t')
    assert len(first_person) == 8

    assert first_person[-1] == 'Study1'


def test_families_data_download_no_permissions(user_client):
    url = '/api/v3/common_reports/families_data/study4'
    response = user_client.get(url)

    assert response
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_families_data_download_not_found(user_client):
    url = '/api/v3/common_reports/families_data/Study4'
    response = user_client.get(url)

    assert response
    assert response.status_code == status.HTTP_404_NOT_FOUND
