def test_user_client_no_access(user_client, mock_gpf_instance):
    response = user_client.get('/api/v3/dataset_details/inheritance_trio')

    assert response
    assert response.status_code == 403


def test_admin_client_get_study(admin_client, mock_gpf_instance):
    response = admin_client.get('/api/v3/dataset_details/inheritance_trio')

    assert response
    assert response.status_code == 200
    assert response.data['hasDenovo']


def test_admin_client_get_nonexistant_study(admin_client, mock_gpf_instance):
    response = admin_client.get('/api/v3/dataset_details/asdfghjkl')

    assert response
    assert response.status_code == 400
