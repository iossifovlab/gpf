import pytest
from django.core.urlresolvers import reverse
from rest_framework import status


@pytest.fixture()
def groups_endpoint():
    return reverse('groups-list')


def test_admin_can_get_groups(admin_client, groups_endpoint):
    response = admin_client.get(groups_endpoint)
    assert response.status_code is status.HTTP_200_OK
    assert len(response.data['results']) > 0


def test_user_cant_see_groups(user_client, groups_endpoint):
    response = user_client.get(groups_endpoint)
    assert response.status_code is status.HTTP_403_FORBIDDEN


def test_groups_have_ids_and_names(admin_client, groups_endpoint):
    response = admin_client.get(groups_endpoint)

    assert len(response.data['results']) > 0
    for group in response.data['results']:
        assert 'id' in group
        assert 'name' in group
