from guardian.models import Group
import pytest
from django.core.urlresolvers import reverse

from datasets_api.models import Dataset


@pytest.fixture()
def groups_endpoint():
    return reverse('groups-list')


@pytest.fixture()
def groups_instance_url():
    return group_url


def group_url(group_id):
    return reverse('groups-detail', kwargs={'pk': group_id})


@pytest.fixture()
def grant_permission_url():
    return reverse('grant_permission')


@pytest.fixture()
def revoke_permission_url():
    return reverse('revoke_permission')


@pytest.fixture()
def groups_model():
    return Group


@pytest.fixture()
def group(db, groups_model):
    return groups_model.objects.create(name='New Group')


@pytest.fixture()
def group_with_user(db, group, user):
    user.groups.add(group)

    return group, user


@pytest.fixture()
def dataset(db):
    return Dataset.objects.create(dataset_id='My Dataset')
