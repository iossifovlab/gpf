import pytest
from django.core.urlresolvers import reverse


@pytest.fixture()
def users_endpoint():
    return reverse('users-list')


def test_admin_can_get_all_users(logged_admin_client, users_endpoint):
    response = logged_admin_client.get(users_endpoint)
    print(response.data)
    assert len(response.data["results"]) == 2  # dev admin, dev staff
