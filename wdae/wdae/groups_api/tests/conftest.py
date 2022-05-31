import pytest
from django.contrib.auth.models import Group
from datasets_api.models import Dataset


@pytest.fixture()
def group(db):
    return Group.objects.create(name="New Group")


@pytest.fixture()
def group_with_user(db, group, user):
    user.groups.add(group)
    return group, user


@pytest.fixture()
def dataset(db):
    return Dataset.objects.create(dataset_id="My Dataset")
