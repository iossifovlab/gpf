import pytest
from django.core.urlresolvers import reverse
from rest_framework import status


@pytest.fixture()
def users_endpoint():
    return reverse('users-list')


@pytest.fixture()
def new_user(logged_admin_client, users_endpoint, user_model):
    data = {
        'email': 'new@new.com',
    }
    logged_admin_client.post(users_endpoint, data=data)

    return user_model.objects.get(email='new@new.com')


def test_admin_can_get_default_users(logged_admin_client, users_endpoint):
    response = logged_admin_client.get(users_endpoint)
    assert response.status_code is status.HTTP_200_OK


def test_admin_sees_all_default_users(logged_admin_client, users_endpoint):
    response = logged_admin_client.get(users_endpoint)
    assert response.status_code is status.HTTP_200_OK
    assert len(response.data['results']) is 2  # dev admin, dev staff


def test_all_users_have_groups(logged_admin_client, users_endpoint):
    response = logged_admin_client.get(users_endpoint)
    assert response.status_code is status.HTTP_200_OK

    users = response.data['results']
    assert len(users) > 0
    for user in users:
        assert "groups" in user


def test_users_cant_get_default_users(logged_user_client, users_endpoint):
    response = logged_user_client.get(users_endpoint)
    assert response.status_code is status.HTTP_403_FORBIDDEN


def test_unauthenticated_cant_get_default_users(client, users_endpoint):
    response = client.get(users_endpoint)
    assert response.status_code is status.HTTP_403_FORBIDDEN


def test_admin_can_create_new_users(logged_admin_client, users_endpoint,
                                    user_model):
    data = {
        'email': 'new@new.com',
    }
    response = logged_admin_client.post(users_endpoint, data=data)

    assert response.status_code is status.HTTP_201_CREATED
    assert user_model.objects.get(email='new@new.com') is not None


def test_admin_can_see_newly_created_user(logged_admin_client, users_endpoint):
    default_users = logged_admin_client.get(users_endpoint).data['results']

    data = {
        'email': 'new@new.com',
    }
    logged_admin_client.post(users_endpoint, data=data)

    new_users = logged_admin_client.get(users_endpoint).data['results']
    assert len(new_users) is len(default_users) + 1


def test_new_user_is_not_active(new_user):
    assert not new_user.is_active
