import pytest
from django.core.urlresolvers import reverse
from rest_framework import status
from django.contrib.auth.models import Group


@pytest.fixture()
def users_endpoint():
    return reverse('users-list')


@pytest.fixture()
def users_instance_url():
    return user_url


@pytest.fixture()
def user_remove_password_endpoint():
    return user_remove_password_url


def user_remove_password_url(user_id):
    return reverse('users-remove-password', kwargs={'pk': user_id})


def user_url(user_id):
    return reverse('users-detail', kwargs={'pk': user_id})


@pytest.fixture()
def active_user(db, user_model):
    user = user_model.objects.create(email='new@new.com', password='secret')

    assert user.is_active
    return user


@pytest.fixture()
def inactive_user(db, user_model):
    user = user_model.objects.create(email='new@new.com')

    assert not user.is_active
    return user


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


def test_users_cant_get_all_users(user_client, users_endpoint):
    response = user_client.get(users_endpoint)
    assert response.status_code is status.HTTP_403_FORBIDDEN


def test_unauthenticated_cant_get_all_users(client, users_endpoint):
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
    old_users = admin_client.get(users_endpoint).data['results']

    data = {
        'email': 'new@new.com',
    }
    admin_client.post(users_endpoint, data=data)

    new_users = admin_client.get(users_endpoint).data['results']
    assert len(new_users) == len(old_users) + 1


def test_new_user_is_not_active(admin_client, users_endpoint):
    old_users = admin_client.get(users_endpoint).data['results']

    data = {
        'email': 'new@new.com',
    }
    admin_client.post(users_endpoint, data=data)

    new_users = admin_client.get(users_endpoint).data['results']
    assert len(new_users) == len(old_users) + 1

    new_user = filter(lambda u: u['email'] == data['email'], new_users)[0]
    assert not new_user['hasPassword']


def test_admin_can_partial_update_user(admin_client, users_instance_url,
                                       user_model):
    data = {
        'name': 'Ivan'
    }
    user = user_model.objects.first()

    response = admin_client.patch(
        users_instance_url(user.pk), data, format='json')
    print(response)
    assert response.status_code is status.HTTP_200_OK

    user.refresh_from_db()
    assert user.name == 'Ivan'


def test_admin_cant_partial_update_user_email(
        admin_client, users_instance_url, user_model):
    data = {
        'email': 'test@test.com'
    }
    user = user_model.objects.first()
    assert user.email != data['email']
    old_email = user.email

    response = admin_client.patch(
        users_instance_url(user.pk), data, format='json')
    assert response.status_code is status.HTTP_400_BAD_REQUEST

    user.refresh_from_db()
    assert user.email == old_email


def test_admin_can_add_user_group(admin_client, users_instance_url, user_model):
    new_group = Group.objects.create(name='brand_new_group')
    user = user_model.objects.last()

    data = {
        'groups': [
            {
                'id': new_group.id,
                'name': new_group.name,
            }
        ]
    }
    assert not user.groups.filter(name=new_group.name).exists()

    response = admin_client.put(users_instance_url(user.pk), data,
                                format='json')
    print(response)
    assert response.status_code is status.HTTP_200_OK

    user.refresh_from_db()
    assert user.groups.filter(name=new_group.name).exists()


def test_admin_can_remove_user_group(admin_client, users_instance_url, user_model):
    user = user_model.objects.last()
    assert user.groups.count() > 0
    first_group = user.groups.first()

    data = {
        'groups': [
            {
                'id': group.id,
                'name': group.name,
            } for group in user.groups.exclude(id=first_group.id).all()
        ]
    }

    response = admin_client.put(users_instance_url(user.pk), data,
                                format='json')
    print(response)
    assert response.status_code is status.HTTP_200_OK

    user.refresh_from_db()
    assert not user.groups.filter(id=first_group.id).exists()


def test_admin_can_remove_password_of_user(
        admin_client, active_user, user_remove_password_endpoint):
    assert active_user.has_usable_password()

    response = admin_client.post(
        user_remove_password_endpoint(active_user.pk))

    assert response.status_code is status.HTTP_204_NO_CONTENT

    active_user.refresh_from_db()
    assert not active_user.has_usable_password()
    assert not active_user.is_active


def test_user_cant_remove_other_user_password(
        user_client, user_remove_password_endpoint, active_user):
    assert active_user.has_usable_password()

    response = user_client.post(
        user_remove_password_endpoint(active_user.pk))

    assert response.status_code is status.HTTP_403_FORBIDDEN

    active_user.refresh_from_db()
    assert active_user.has_usable_password()
    assert active_user.is_active


def test_anonymous_user_cant_remove_other_user_password(
        client, user_remove_password_endpoint, active_user):
    assert active_user.has_usable_password()

    response = client.post(
        user_remove_password_endpoint(active_user.pk))

    assert response.status_code is status.HTTP_403_FORBIDDEN

    active_user.refresh_from_db()
    assert active_user.has_usable_password()
    assert active_user.is_active


def test_inactive_user_stays_inactive(
        admin_client, user_remove_password_endpoint, inactive_user):
    assert not inactive_user.has_usable_password()

    response = admin_client.post(
        user_remove_password_endpoint(inactive_user.pk))

    assert response.status_code is status.HTTP_204_NO_CONTENT

    inactive_user.refresh_from_db()
    assert not inactive_user.has_usable_password()
    assert not inactive_user.is_active
