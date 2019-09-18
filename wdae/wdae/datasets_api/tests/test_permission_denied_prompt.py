import pytest


pytestmark = pytest.mark.usefixtures("mock_studies_manager")


def test_permission_denied_prompt_through_user_client(user_client):
    response = user_client.get('/api/v3/datasets/denied_prompt')

    assert response
    assert response.status_code == 200
    assert response.data['data'] == \
        ('This is a real permission denied prompt.'
         ' The view has successfully sent the prompt.\n')
