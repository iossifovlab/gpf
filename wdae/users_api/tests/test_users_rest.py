import pytest
from django.core.urlresolvers import reverse
from rest_framework import status


@pytest.fixture()
def users_endpoint():
    return reverse('users-list')


def test_admin_can_get_default_users(logged_admin_client, users_endpoint):
    response = logged_admin_client.get(users_endpoint)
    assert response.status_code == status.HTTP_200_OK


def test_admin_sees_all_default_users(logged_admin_client, users_endpoint):
    response = logged_admin_client.get(users_endpoint)
    assert len(response.data["results"]) == 2  # dev admin, dev staff


def test_users_cant_get_default_users(logged_user_client, users_endpoint):
    response = logged_user_client.get(users_endpoint)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_unauthenticated_cant_get_default_users(client, users_endpoint):
    response = client.get(users_endpoint)
    assert response.status_code == status.HTTP_403_FORBIDDEN
