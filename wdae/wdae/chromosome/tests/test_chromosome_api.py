import pytest

pytestmark = pytest.mark.usefixtures('mock_gpf_instance')

def test_chromosome_api_get(user_client, chromosome_test_data):
    response = user_client.get('/api/v3/chromosomes')

    assert response
    assert response.status_code == 200
    assert response.data == chromosome_test_data
