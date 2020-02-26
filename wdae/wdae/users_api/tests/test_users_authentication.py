import json

from rest_framework import status


def test_successful_auth(user, client):
    url = '/api/v3/users/login'
    data = {
        'username': 'user@example.com',
        'password': 'secret',
    }

    response = client.post(
        url, json.dumps(data), content_type='application/json', format='json')

    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_successful_auth_case_insensitive(user, client):
    url = '/api/v3/users/login'
    data = {
        'username': 'UsER@ExAmPlE.cOm',
        'password': 'secret',
    }

    response = client.post(
        url, json.dumps(data), content_type='application/json', format='json')

    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_failed_auth(user, client):
    url = '/api/v3/users/login'
    data = {
        'username': 'bad@example.com',
        'password': 'secret'
    }

    response = client.post(

        url, json.dumps(data), content_type='application/json', format='json')
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_user_info_after_auth(user, client):
    user.is_staff = True
    user.save()

    url = '/api/v3/users/login'
    data = {
        'username': 'user@example.com',
        'password': 'secret',
    }

    response = client.post(
        url, json.dumps(data), content_type='application/json', format='json')

    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = client.get('/api/v3/users/get_user_info')
    assert response.data['loggedIn'] is True
    assert response.data['email'] == 'user@example.com'
