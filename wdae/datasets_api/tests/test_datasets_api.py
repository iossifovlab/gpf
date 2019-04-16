import pytest

pytestmark = pytest.mark.usefixtures("mock_studies_manager")


def test_datasets_api_get_all(admin_client):
    response = admin_client.get('/api/v3/datasets')

    assert response
    assert response.status_code == 200
    assert len(response.data['data']) == 6


def test_datasets_api_get_one(admin_client):
    response = admin_client.get('/api/v3/datasets/quads_in_parent')
    print(response.data)
    assert response
    assert response.status_code == 200
    assert response.data['data']['accessRights'] is True
    assert response.data['data']['name'] == 'QUADS_IN_PARENT'


def test_datasets_api_get_404(admin_client):
    response = admin_client.get('/api/v3/datasets/alabala')

    assert response
    assert response.status_code == 404
    assert response.data['error'] == 'Dataset alabala not found'


def test_datasets_api_get_forbiden(user_client):
    response = user_client.get('/api/v3/datasets/quads_in_parent')

    assert response
    assert response.status_code == 200
    assert response.data['data']['accessRights'] is False
    assert response.data['data']['name'] == 'QUADS_IN_PARENT'


def test_datasets_name_ordering(admin_client):
    response = admin_client.get('/api/v3/datasets')

    assert response
    assert response.status_code == 200

    sorted_response_data = sorted(response.data['data'],
                                  key=lambda d: d['name'])
    assert response.data['data'] == sorted_response_data
