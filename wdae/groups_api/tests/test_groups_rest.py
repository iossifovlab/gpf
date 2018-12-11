from __future__ import print_function
from builtins import next

from guardian.models import Group
from guardian import shortcuts
from rest_framework import status

from guardian.shortcuts import assign_perm
from guardian.shortcuts import get_perms
from datasets_api.models import Dataset


def test_admin_can_get_groups(admin_client, groups_endpoint):
    response = admin_client.get(groups_endpoint)
    assert response.status_code is status.HTTP_200_OK
    assert len(response.data) > 0


def test_user_cant_see_groups(user_client, groups_endpoint):
    response = user_client.get(groups_endpoint)
    assert response.status_code is status.HTTP_403_FORBIDDEN


def test_groups_have_ids_and_names(admin_client, groups_endpoint):
    response = admin_client.get(groups_endpoint)
    assert response.status_code is status.HTTP_200_OK

    assert len(response.data) > 0
    for group in response.data:
        assert 'id' in group
        assert 'name' in group


def test_groups_have_users_and_datasets(admin_client, groups_endpoint):
    response = admin_client.get(groups_endpoint)
    assert response.status_code is status.HTTP_200_OK

    assert len(response.data) > 0
    for group in response.data:
        assert 'users' in group
        assert 'datasets' in group


def test_single_group_has_users_and_datasets(admin_client, groups_instance_url):
    groups = Group.objects.all()
    for group in groups:
        response = admin_client.get(groups_instance_url(group.id))
        assert response.status_code is status.HTTP_200_OK
        assert 'users' in response.data
        assert 'datasets' in response.data


def test_admin_cant_delete_groups(admin_client, groups_endpoint,
                                  groups_instance_url, groups_model):
    all_groups = groups_model.objects.all()
    assert len(all_groups) > 0

    for group in all_groups:
        del_response = admin_client.delete(
            groups_instance_url(group.pk),
            format='json')

        assert del_response.status_code is status.HTTP_405_METHOD_NOT_ALLOWED

    response = admin_client.get(groups_endpoint)
    assert response.status_code is status.HTTP_200_OK

    assert len(response.data) is len(all_groups)


def test_admin_cant_create_groups(admin_client, groups_endpoint):
    data = {
        'name': 'NewAwesomeGroup'
    }

    response = admin_client.post(groups_endpoint, data=data, format='json')

    assert response.status_code is status.HTTP_405_METHOD_NOT_ALLOWED


def test_admin_can_rename_groups(
        admin_client, groups_instance_url, group_with_user):
    group, _ = group_with_user
    assert group is not None

    test_name = 'AwesomeGroup'
    assert group.name is not test_name

    data = {
        'id': group.id,
        'name': test_name
    }

    response = admin_client.put(groups_instance_url(group.pk),
                                data=data)
    print(response)
    assert response.status_code is status.HTTP_200_OK
    assert response.data['name'] == test_name

    group.refresh_from_db()
    assert group.name == test_name


def test_group_has_all_users(admin_client, groups_instance_url, group):
    test_emails = ['test@email.com', 'other@email.com', 'last@example.com']
    for email in test_emails:
        group.user_set.create(email=email)

    response = admin_client.get(groups_instance_url(group.id))
    assert response.status_code is status.HTTP_200_OK
    for email in test_emails:
        assert email in response.data['users']


def test_no_empty_groups_are_accessible(
        admin_client, groups_endpoint, groups_instance_url):
    groups_count = Group.objects.count()
    new_group = Group.objects.create(name='New Group')

    response = admin_client.get(groups_endpoint)
    assert response.status_code is status.HTTP_200_OK
    assert len(response.data) == groups_count

    response = admin_client.get(groups_instance_url(new_group.id))
    assert response.status_code is status.HTTP_404_NOT_FOUND


def test_empty_group_with_permissions_is_shown(
        admin_client, groups_endpoint, dataset):
    groups_count = Group.objects.count()
    group = Group.objects.create(name='New Group')

    shortcuts.assign_perm('view', group, dataset)

    response = admin_client.get(groups_endpoint)
    assert response.status_code is status.HTTP_200_OK
    assert len(response.data) == groups_count + 1
    new_group_reponse = next(
        (response_group for response_group in response.data
         if response_group['name'] == group.name),
        None)
    assert new_group_reponse
    assert new_group_reponse['datasets'][0] == dataset.dataset_id


def test_group_has_all_datasets(
        admin_client, groups_instance_url, group_with_user, dataset):
    group, _ = group_with_user

    response = admin_client.get(groups_instance_url(group.id))
    assert response.status_code is status.HTTP_200_OK
    assert len(response.data['datasets']) == 0

    shortcuts.assign_perm('view', group, dataset)

    response = admin_client.get(groups_instance_url(group.id))
    assert response.status_code is status.HTTP_200_OK
    assert len(response.data['datasets']) == 1
    assert response.data['datasets'][0] == dataset.dataset_id


def test_grant_permission_for_group(
        admin_client, group_with_user, grant_permission_url, dataset):
    group, user = group_with_user
    data = {
        'datasetId': dataset.dataset_id,
        'groupName': group.name
    }

    assert not user.has_perm('view', dataset)

    response = admin_client.post(grant_permission_url, data, format='json')

    assert response.status_code == status.HTTP_200_OK
    assert user.has_perm('view', dataset)


def test_grant_permission_creates_new_group(
        admin_client, user, grant_permission_url, dataset):
    groupName = 'NewGroup'
    data = {
        'datasetId': dataset.dataset_id,
        'groupName': groupName
    }

    assert not user.has_perm('view', dataset)

    response = admin_client.post(grant_permission_url, data, format='json')

    assert response.status_code == status.HTTP_200_OK
    assert Group.objects.filter(name=groupName).count() == 1


def test_not_admin_cant_grant_permissions(
        user_client, group_with_user, grant_permission_url, dataset):
    group, user = group_with_user
    data = {
        'datasetId': dataset.dataset_id,
        'groupName': group.name
    }

    assert not user.has_perm('view', dataset)

    response = user_client.post(grant_permission_url, data, format='json')

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert not user.has_perm('view', dataset)


def test_not_admin_grant_permissions_does_not_create_group(
        user_client, grant_permission_url, dataset):
    groupName = 'NewGroup'
    data = {
        'datasetId': dataset.dataset_id,
        'groupName': groupName
    }

    response = user_client.post(grant_permission_url, data, format='json')

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Group.objects.filter(name=groupName).count() == 0


def test_revoke_permission_for_group(
        admin_client, group_with_user, revoke_permission_url, dataset):
    group, user = group_with_user
    data = {
        'datasetId': dataset.dataset_id,
        'groupId': group.id
    }

    assign_perm('view', group, dataset)

    assert user.has_perm('view', dataset)

    response = admin_client.post(revoke_permission_url, data, format='json')

    assert response.status_code == status.HTTP_200_OK
    assert not user.has_perm('view', dataset)


def test_not_admin_cant_revoke_permissions(
        user_client, group_with_user, revoke_permission_url, dataset):
    group, user = group_with_user
    data = {
        'datasetId': dataset.dataset_id,
        'groupId': group.id
    }
    assign_perm('view', group, dataset)

    assert user.has_perm('view', dataset)

    response = user_client.post(revoke_permission_url, data, format='json')

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert user.has_perm('view', dataset)


def test_cant_revoke_default_permissions(
        user_client, revoke_permission_url, dataset):
    Dataset.recreate_dataset_perm(dataset.dataset_id, [])

    assert len(dataset.default_groups) > 0

    for group_name in dataset.default_groups:
        group = Group.objects.get(name=group_name)
        data = {
            'datasetId': dataset.dataset_id,
            'groupId': group.id
        }

        response = user_client.post(revoke_permission_url, data, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'view' in get_perms(group, dataset)
