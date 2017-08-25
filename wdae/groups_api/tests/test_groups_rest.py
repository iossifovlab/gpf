from functools import partial
import pytest
from django.core.urlresolvers import reverse
from guardian.models import Group
from rest_framework import status


@pytest.fixture()
def groups_endpoint():
    return reverse('groups-list')


@pytest.fixture()
def groups_instance_url(groups_endpoint):
    return partial(group_url, groups_endpoint)


@pytest.fixture()
def groups_model():
    return Group


def group_url(groups_endpoint, group_id):
    return '{}/{}'.format(groups_endpoint, group_id)


def test_admin_can_get_groups(admin_client, groups_endpoint):
    response = admin_client.get(groups_endpoint)
    assert response.status_code is status.HTTP_200_OK
    assert len(response.data['results']) > 0


def test_user_cant_see_groups(user_client, groups_endpoint):
    response = user_client.get(groups_endpoint)
    assert response.status_code is status.HTTP_403_FORBIDDEN


def test_groups_have_ids_and_names(admin_client, groups_endpoint):
    response = admin_client.get(groups_endpoint)
    assert response.status_code is status.HTTP_200_OK

    assert len(response.data['results']) > 0
    for group in response.data['results']:
        assert 'id' in group
        assert 'name' in group


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

    assert len(response.data['results']) is len(all_groups)


def test_admin_cant_create_groups(admin_client, groups_endpoint):
    data = {
        'name': 'NewAwesomeGroup'
    }

    response = admin_client.post(groups_endpoint, data=data, format='json')

    assert response.status_code is status.HTTP_405_METHOD_NOT_ALLOWED


def test_admin_can_rename_groups(admin_client, groups_instance_url, groups_model):
    first_group = groups_model.objects.first()
    assert first_group is not None

    test_name = 'AwesomeGroup'
    assert first_group.name is not test_name

    data = {
        'name': test_name
    }

    response = admin_client.put(groups_instance_url(first_group.pk),
                                data=data)

    assert response.status_code is status.HTTP_200_OK
    assert response.data['name'] == test_name

    first_group.refresh_from_db()
    assert first_group.name == test_name
