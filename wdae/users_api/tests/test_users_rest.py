import pytest
from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth.models import Group


@pytest.fixture()
def users_endpoint():
    return reverse('users-list')


@pytest.fixture()
def users_instance_url():
    return user_url


def user_url(user_id):
    return reverse('users-detail', kwargs={'pk': user_id})


@pytest.fixture()
def user_remove_password_endpoint():
    return user_remove_password_url


def user_remove_password_url(user_id):
    return reverse('users-password-remove', kwargs={'pk': user_id})


@pytest.fixture()
def user_reset_password_endpoint():
    return user_reset_password_url


def user_reset_password_url(user_id):
    return reverse('users-password-reset', kwargs={'pk': user_id})


@pytest.fixture()
def users_bulk_add_group_url():
    return reverse('users-bulk-add-group')


@pytest.fixture()
def users_bulk_remove_group_url():
    return reverse('users-bulk-remove-group')


@pytest.fixture()
def empty_group(db):
    return Group.objects.create(name='Empty group')


@pytest.fixture()
def active_user(db, user_model):
    user = user_model.objects.create_user(email='new@new.com', password='secret')

    assert user.is_active
    return user


@pytest.fixture()
def inactive_user(db, user_model):
    user = user_model.objects.create_user(email='new@new.com')

    assert not user.is_active
    return user


@pytest.fixture()
def three_new_users(db, user_model):
    users = []
    for email_id in range(3):
        user = user_model.objects \
            .create(email='user{}@example.com'.format(email_id+1))
        users.append(user)

    return users


@pytest.fixture()
def three_users_in_a_group(db, three_new_users, empty_group):
    empty_group.user_set.add(*three_new_users)
    for user in three_new_users:
        user.refresh_from_db()

    return three_new_users, empty_group


@pytest.fixture()
def logged_in_user(active_user):
    client = APIClient()
    client.login(email=active_user.email, password='secret')
    return active_user, client


def test_admin_can_get_default_users(admin_client, users_endpoint):
    response = admin_client.get(users_endpoint)
    assert response.status_code is status.HTTP_200_OK


def test_admin_sees_all_default_users(admin_client, users_endpoint):
    response = admin_client.get(users_endpoint)
    assert response.status_code is status.HTTP_200_OK
    assert len(response.data) is 2  # dev admin, dev staff


def test_all_users_have_groups(admin_client, users_endpoint):
    response = admin_client.get(users_endpoint)
    assert response.status_code is status.HTTP_200_OK

    users = response.data
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


def test_new_user_name_can_be_blank(admin_client, users_endpoint, user_model):
    data = {
        'email': 'new@new.com',
        'name': ''
    }
    response = admin_client.post(users_endpoint, data=data)

    print(response)
    assert response.status_code is status.HTTP_201_CREATED
    assert user_model.objects.get(email='new@new.com') is not None


def test_admin_can_create_new_user_with_groups(
        admin_client, users_endpoint, user_model, empty_group):
    data = {
        'email': 'new@new.com',
        'groups': [empty_group.name]
    }
    response = admin_client.post(users_endpoint, data=data, format='json')

    print(response)
    assert response.status_code is status.HTTP_201_CREATED
    assert user_model.objects.get(email='new@new.com') is not None

    user = user_model.objects.get(email='new@new.com')
    assert user.groups.filter(pk=empty_group.id).exists()


def test_admin_can_see_newly_created_user(admin_client, users_endpoint):
    old_users = admin_client.get(users_endpoint).data

    data = {
        'email': 'new@new.com',
    }
    admin_client.post(users_endpoint, data=data)

    new_users = admin_client.get(users_endpoint).data
    assert len(new_users) == len(old_users) + 1


def test_new_user_is_not_active(admin_client, users_endpoint):
    old_users = admin_client.get(users_endpoint).data

    data = {
        'email': 'new@new.com',
    }
    admin_client.post(users_endpoint, data=data)

    new_users = admin_client.get(users_endpoint).data
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


def test_user_name_can_be_updated_to_blank(
        admin_client, users_instance_url, active_user):
    data = {
        'id': active_user.id,
        'name': '',
        'groups': [group.name for group in active_user.groups.all()]
    }
    print(data['groups'])

    response = admin_client.put(
        users_instance_url(active_user.id), data, format='json')
    print(response)
    assert response.status_code is status.HTTP_200_OK

    active_user.refresh_from_db()
    assert active_user.name == ''


def test_admin_can_add_user_group(
        admin_client, users_instance_url, active_user, empty_group):
    user = active_user

    data = {
        'groups': [empty_group.name]
    }
    data['groups'] += [
        g.name for g in user.protected_groups
    ]

    assert not user.groups.filter(name=empty_group.name).exists()
    response = admin_client.put(users_instance_url(user.pk), data,
                                format='json')
    print(response)
    assert response.status_code is status.HTTP_200_OK

    user.refresh_from_db()
    assert user.groups.filter(name=empty_group.name).exists()


def test_admin_can_update_with_new_group(
    admin_client, users_instance_url, active_user):
    group_name = 'new group'
    user = active_user

    data = {
        'groups': [group_name]
    }
    data['groups'] += [
        g.name for g in user.protected_groups
    ]

    assert not Group.objects.filter(name=group_name).exists()
    response = admin_client.put(users_instance_url(user.pk), data,
                                format='json')
    print(response)
    assert response.status_code is status.HTTP_200_OK

    user.refresh_from_db()
    assert Group.objects.filter(name=group_name).exists()
    assert user.groups.filter(name=group_name).exists()


def test_admin_can_remove_user_group(
        admin_client, users_instance_url, empty_group, active_user):
    active_user.groups.add(empty_group)

    data = {
        'groups': [
            group.name
            for group in active_user.groups.exclude(id=empty_group.id).all()
        ]
    }
    response = admin_client.put(
        users_instance_url(active_user.pk), data, format='json')

    assert response.status_code is status.HTTP_200_OK

    active_user.refresh_from_db()
    assert not active_user.groups.filter(id=empty_group.id).exists()


def test_protected_groups_cant_be_removed(
        admin_client, users_instance_url, empty_group, active_user):
    data = {
        'groups': [empty_group.name]
    }
    response = admin_client.put(
        users_instance_url(active_user.pk), data, format='json')

    assert response.status_code is status.HTTP_400_BAD_REQUEST

    assert active_user.protected_groups.count() == 2
    assert not active_user.groups.filter(id=empty_group.id).exists()


def test_admin_can_delete_user(admin_client, users_instance_url, user_model):
    user = user_model.objects.create(email='test@test.com')
    user_id = user.pk
    assert user_model.objects.filter(pk=user_id).exists()

    response = admin_client.delete(users_instance_url(user_id))

    assert response.status_code is status.HTTP_204_NO_CONTENT
    assert not user_model.objects.filter(pk=user_id).exists()


def test_admin_can_remove_password_of_user(
        admin_client, active_user, user_remove_password_endpoint):
    assert active_user.has_usable_password()

    response = admin_client.post(
        user_remove_password_endpoint(active_user.pk))

    assert response.status_code is status.HTTP_204_NO_CONTENT

    active_user.refresh_from_db()
    assert not active_user.has_usable_password()
    assert not active_user.is_active


def test_removing_user_password_deauthenticates_them(
        admin_client, logged_in_user, user_remove_password_endpoint):
    user, user_client = logged_in_user
    response = user_client.get('/api/v3/users/get_user_info')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['loggedIn']

    url = user_remove_password_endpoint(user.pk)

    response = admin_client.post(url)
    assert response.status_code is status.HTTP_204_NO_CONTENT

    response = user_client.get('/api/v3/users/get_user_info')
    assert response.status_code == status.HTTP_200_OK
    assert not response.data['loggedIn']


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


def test_admin_can_reset_user_password(
        admin_client, user_reset_password_endpoint, active_user):
    url = user_reset_password_endpoint(active_user.pk)
    response = admin_client.post(url)

    assert response.status_code is status.HTTP_204_NO_CONTENT

    active_user.refresh_from_db()
    assert not active_user.has_usable_password()
    assert not active_user.is_active


def test_resetting_user_password_deauthenticates_them(
        admin_client, logged_in_user, user_reset_password_endpoint):
    user, user_client = logged_in_user
    response = user_client.get('/api/v3/users/get_user_info')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['loggedIn']

    url = user_reset_password_endpoint(user.pk)

    response = admin_client.post(url)
    assert response.status_code is status.HTTP_204_NO_CONTENT

    response = user_client.get('/api/v3/users/get_user_info')
    assert response.status_code == status.HTTP_200_OK
    assert not response.data['loggedIn']


def test_user_cant_reset_other_user_password(
        user_client, user_reset_password_endpoint, active_user):
    assert active_user.has_usable_password()

    response = user_client.post(
        user_reset_password_endpoint(active_user.pk))

    assert response.status_code is status.HTTP_403_FORBIDDEN

    active_user.refresh_from_db()
    assert active_user.has_usable_password()
    assert active_user.is_active


def test_searching_by_email_finds_only_single_user(
        admin_client, users_endpoint, active_user, user_model):
    assert user_model.objects.count() > 1

    params = {
        'search': active_user.email
    }
    response = admin_client.get(users_endpoint, params)

    assert response.status_code is status.HTTP_200_OK
    assert len(response.data) == 1


def test_searching_by_any_user_finds_all_users(
        admin_client, users_endpoint, active_user, user_model):
    users_count = user_model.objects.count()
    assert users_count > 1

    params = {
        'search': 'any_user'
    }
    response = admin_client.get(users_endpoint, params)

    assert response.status_code is status.HTTP_200_OK
    assert len(response.data) == users_count


def test_searching_by_username(admin_client, users_endpoint, active_user):
    active_user.name = 'Testy Mc Testington'
    active_user.save()

    params = {
        'search': 'test'
    }
    response = admin_client.get(users_endpoint, params)
    assert response.status_code is status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]['id'] == active_user.id


def test_searching_by_email(admin_client, users_endpoint, active_user):
    params = {
        'search': active_user.email[:8]
    }
    response = admin_client.get(users_endpoint, params)
    assert response.status_code is status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]['id'] == active_user.id


def test_bulk_adding_users_to_existing_group(
        admin_client, users_bulk_add_group_url, three_new_users, empty_group):
    for user in three_new_users:
        assert not user.groups.filter(name=empty_group.name).exists()

    data = {
        'userIds': map(lambda u: u.id, three_new_users),
        'group': empty_group.name
    }

    response = admin_client.post(users_bulk_add_group_url, data, format='json')
    assert response.status_code is status.HTTP_200_OK

    for user in three_new_users:
        user.refresh_from_db()
        assert user.groups.filter(name=empty_group.name).exists()


def test_bulk_adding_users_to_new_group(
        admin_client, users_bulk_add_group_url, three_new_users):
    group_name = 'some random name'
    data = {
        'userIds': map(lambda u: u.id, three_new_users),
        'group': group_name
    }

    response = admin_client.post(users_bulk_add_group_url, data, format='json')
    assert response.status_code is status.HTTP_200_OK

    for user in three_new_users:
        user.refresh_from_db()
        assert user.groups.filter(name=data['group']).exists()

    assert Group.objects.filter(name=group_name).exists()


def test_bulk_adding_with_duplicate_user_ids_fails(
        admin_client, users_bulk_add_group_url, three_new_users):
    data = {
        'userIds': map(lambda u: u.id, three_new_users),
        'group': 'some random name'
    }
    data['userIds'].append(three_new_users[0].id)

    response = admin_client.post(users_bulk_add_group_url, data, format='json')
    assert response.status_code is status.HTTP_400_BAD_REQUEST

    for user in three_new_users:
        user.refresh_from_db()
        assert not user.groups.filter(name=data['group']).exists()


def test_bulk_adding_with_duplicate_user_ids_doesnt_create_new_group(
        admin_client, users_bulk_add_group_url, three_new_users):
    group_name = 'some random name'
    data = {
        'userIds': map(lambda u: u.id, three_new_users),
        'group': group_name
    }
    data['userIds'].append(three_new_users[0].id)

    response = admin_client.post(users_bulk_add_group_url, data, format='json')
    assert response.status_code is status.HTTP_400_BAD_REQUEST

    assert not Group.objects.filter(name=group_name).exists()


def test_bulk_adding_unknown_user_ids_fails(
        admin_client, users_bulk_add_group_url, three_new_users):
    group_name = 'some random name'
    data = {
        'userIds': map(lambda u: u.id, three_new_users),
        'group': group_name
    }
    data['userIds'].append(424242)

    response = admin_client.post(users_bulk_add_group_url, data, format='json')
    assert response.status_code is status.HTTP_400_BAD_REQUEST

    assert not Group.objects.filter(name=group_name).exists()


def test_bulk_remove_group_works(
        admin_client, users_bulk_remove_group_url, three_users_in_a_group):
    users, group = three_users_in_a_group
    data = {
        'userIds': map(lambda u: u.id, users),
        'group': group.name
    }

    response = admin_client.post(
        users_bulk_remove_group_url, data, format='json')
    assert response.status_code is status.HTTP_200_OK

    for user in users:
        assert not user.groups.filter(name=group.name).exists()


def test_bulk_remove_with_user_without_the_group_works(
        admin_client, users_bulk_remove_group_url, three_users_in_a_group,
        active_user):
    users, group = three_users_in_a_group
    assert not active_user.groups.filter(name=group.name).exists()

    data = {
        'userIds': map(lambda u: u.id, users),
        'group': group.name
    }
    data['userIds'].append(active_user.id)

    response = admin_client.post(
        users_bulk_remove_group_url, data, format='json')
    assert response.status_code is status.HTTP_200_OK

    for user in users:
        assert not user.groups.filter(name=group.name).exists()
    assert not active_user.groups.filter(name=group.name).exists()


def test_bulk_remove_unknown_group_fails(
        admin_client, users_bulk_remove_group_url, three_users_in_a_group):
    users, _ = three_users_in_a_group
    data = {
        'userIds': map(lambda u: u.id, users),
        'group': 'alabala'
    }

    response = admin_client.post(
        users_bulk_remove_group_url, data, format='json')
    assert response.status_code is status.HTTP_404_NOT_FOUND
