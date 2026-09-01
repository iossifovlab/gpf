# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from datasets_api.models import Dataset
from django.contrib.auth.models import Group
from gpf_instance.gpf_instance import WGPFInstance
from users_api.models import WdaeUser


@pytest.fixture
def group(db: None) -> Group:  # ruff: ignore[unused-function-argument]
    return Group.objects.create(name="New Group")


@pytest.fixture
def group_with_user(
    db: None,  # ruff: ignore[unused-function-argument]
    group: Group,
    user: WdaeUser,
) -> tuple[Group, WdaeUser]:
    user.groups.add(group)
    return group, user


@pytest.fixture
def dataset(
    db: None,  # ruff: ignore[unused-function-argument]
    t4c8_wgpf_instance: WGPFInstance,  # ruff: ignore[unused-function-argument]
) -> Dataset:
    # pylint: disable=no-member
    return Dataset.objects.get(dataset_id="t4c8_dataset")
