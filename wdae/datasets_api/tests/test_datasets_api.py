import pytest


@pytest.mark.django_db(transaction=True)
def test_datasets_api_get_all(client):
    response = client.get('/api/v3/datasets')

    assert response
    assert response.status_code == 200
    assert len(response.data['data']) == 14


@pytest.mark.django_db(transaction=True)
def test_datasets_api_get_one(client):
    response = client.get('/api/v3/datasets/quads_in_parent')

    assert response
    assert response.status_code == 200
    assert response.data['data']['name'] == 'QUADS_IN_PARENT'


@pytest.mark.django_db(transaction=True)
def test_datasets_api_get_404(client):
    response = client.get('/api/v3/datasets/alabala')

    assert response
    assert response.status_code == 404
    assert response.data['error'] == 'Dataset alabala not found'
