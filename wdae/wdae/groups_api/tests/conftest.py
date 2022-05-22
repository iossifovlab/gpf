import pytest

from django.contrib.auth.models import Group

from datasets_api.models import Dataset


@pytest.fixture()
def groups_model():
    return Group


@pytest.fixture()
def group(db, groups_model):
    return groups_model.objects.create(name="New Group")


@pytest.fixture()
def group_with_user(db, group, user):
    user.groups.add(group)

    return group, user


@pytest.fixture()
def dataset(db):
    return Dataset.objects.create(dataset_id="My Dataset")
