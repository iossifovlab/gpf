# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from datasets_api.models import Dataset
from django.contrib.auth.models import Group


@pytest.fixture()
def group(db):
    return Group.objects.create(name="New Group")


@pytest.fixture()
def group_with_user(db, group, user):
    user.groups.add(group)
    return group, user


@pytest.fixture()
def dataset(wdae_gpf_instance, db):
    # pylint: disable=no-member
    return Dataset.objects.get(dataset_id="Dataset1")
