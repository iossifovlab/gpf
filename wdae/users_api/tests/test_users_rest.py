from functools import partial
import pytest
from django.core.urlresolvers import reverse
from rest_framework import status

from users_api.models import WdaeUser


@pytest.fixture()
def users_endpoint():
    return reverse('users-list')


@pytest.fixture()
def users_instance_url(users_endpoint):
    return partial(user_url, users_endpoint)


def user_url(users_endpoint, user_id):
    return '{}/{}'.format(users_endpoint, user_id)


@pytest.fixture()
def new_user(admin_client, users_endpoint, user_model):
    data = {
        'email': 'new@new.com',
    }
    admin_client.post(users_endpoint, data=data)

    return user_model.objects.get(email='new@new.com')


def test_admin_can_get_default_users(admin_client, users_endpoint):
    response = admin_client.get(users_endpoint)
    assert response.status_code is status.HTTP_200_OK


def test_admin_sees_all_default_users(admin_client, users_endpoint):
    response = admin_client.get(users_endpoint)
    assert response.status_code is status.HTTP_200_OK
    assert len(response.data['results']) is 2  # dev admin, dev staff


def test_all_users_have_groups(admin_client, users_endpoint):
    response = admin_client.get(users_endpoint)
    assert response.status_code is status.HTTP_200_OK

    users = response.data['results']
    assert len(users) > 0
    for user in users:
        assert "groups" in user


def test_users_cant_get_default_users(user_client, users_endpoint):
    response = user_client.get(users_endpoint)
    assert response.status_code is status.HTTP_403_FORBIDDEN


def test_unauthenticated_cant_get_default_users(client, users_endpoint):
    response = client.get(users_endpoint)
    assert response.status_code is status.HTTP_403_FORBIDDEN


def test_admin_can_create_new_users(admin_client, users_endpoint,
                                    user_model):
    data = {
        'email': 'new@new.com',
    }
    response = admin_client.post(users_endpoint, data=data)

    print(response)
    assert response.status_code is status.HTTP_201_CREATED
    assert user_model.objects.get(email='new@new.com') is not None


def test_admin_can_see_newly_created_user(admin_client, users_endpoint):
    default_users = admin_client.get(users_endpoint).data['results']

    data = {
        'email': 'new@new.com',
    }
    admin_client.post(users_endpoint, data=data)

    new_users = admin_client.get(users_endpoint).data['results']
    assert len(new_users) is len(default_users) + 1


def test_new_user_is_not_active(new_user):
    assert not new_user.is_active


def test_can_create_researcher(admin_client, users_endpoint, user_model):
    research_id = 'aaa-bbb'
    data = {
        'email': 'new@new.com',
        'researcherId': research_id
    }
    response = admin_client.post(users_endpoint, data=data)

    # print(response)
    assert response.status_code is status.HTTP_201_CREATED
    assert response.data['email'] == data['email']
    assert response.data['researcher'] is True

    new_user = user_model.objects.get(pk=response.data['id'])

    group_name = WdaeUser.get_group_name_for_researcher_id(research_id)

    assert new_user.groups.filter(name=group_name).exists()


def test_admin_cant_update_user(admin_client, users_instance_url, user_model):
    data = {
        'email': 'newmail@domain.com',
        'researcherId': 'some-new-id'
    }
    first_user = user_model.objects.first()
    assert first_user.email != data['email']
    old_email = first_user.email

    response = admin_client.put(users_instance_url(first_user.pk), data)
    assert response.status_code is status.HTTP_405_METHOD_NOT_ALLOWED

    first_user.refresh_from_db()
    assert first_user.email == old_email
