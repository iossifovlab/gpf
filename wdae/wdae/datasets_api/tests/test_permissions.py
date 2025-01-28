# pylint: disable=W0621,C0114,C0116,W0212,W0613,C0415,
from typing import cast

import pytest
from box import Box
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, User
from django.test import override_settings
from gpf_instance.gpf_instance import WGPFInstance
from studies.study_wrapper import StudyWrapper

from dae.studies.study import GenotypeData, GenotypeDataGroup
from datasets_api.models import Dataset
from datasets_api.permissions import (
    add_group_perm_to_dataset,
    add_group_perm_to_user,
    get_dataset_groups,
    get_user_groups,
    user_has_permission,
)


@pytest.fixture()
def omni_dataset(custom_wgpf: WGPFInstance) -> GenotypeData:
    """Easy-access fixture for the dataset containing all genotype data."""
    return custom_wgpf.get_genotype_data("omni_dataset")


@pytest.fixture()
def na_user(
    db: None,  # noqa: ARG001
) -> User:
    user_ctr = get_user_model()
    user = user_ctr.objects.create(
        email="nauser@example.com",
        name="Non-Active User",
        is_staff=False,
        is_active=False,
        is_superuser=False,
    )
    user.save()
    return cast(User, user)


def test_parents(custom_wgpf: WGPFInstance) -> None:
    omni_dataset = custom_wgpf.get_genotype_data("omni_dataset")
    assert omni_dataset.parents == set()

    dataset1 = custom_wgpf.get_genotype_data("dataset_1")
    assert dataset1.parents == {"omni_dataset"}

    dataset2 = custom_wgpf.get_genotype_data("dataset_2")
    assert dataset2.parents == {"omni_dataset"}

    study1 = custom_wgpf.get_genotype_data("t4c8_study_1")
    assert study1.parents == {"t4c8_dataset", "dataset_1"}

    study2 = custom_wgpf.get_genotype_data("t4c8_study_2")
    assert study2.parents == {"t4c8_dataset", "dataset_2"}


def test_datasets_studies_ids(omni_dataset: GenotypeData) -> None:
    study_ids = omni_dataset.get_studies_ids()
    assert set(study_ids) == {"omni_dataset",
                              "dataset_1", "dataset_2",
                              "t4c8_study_1", "t4c8_study_2"}

    study_ids = omni_dataset.get_studies_ids(leaves=False)
    assert set(study_ids) == {"omni_dataset",
                              "dataset_1", "dataset_2"}


def test_basic_rights(user: User, omni_dataset: GenotypeData) -> None:
    assert not user_has_permission("t4c8_instance", user, omni_dataset.study_id)
    add_group_perm_to_user(omni_dataset.study_id, user)
    assert user_has_permission("t4c8_instance", user, omni_dataset.study_id)


def test_permissions_give_access_to_parent(
    user: User, omni_dataset: GenotypeData,
) -> None:
    add_group_perm_to_user("dataset_1", user)
    assert user_has_permission("t4c8_instance", user, omni_dataset.study_id)


def test_dataset_group_rights(user: User, omni_dataset: GenotypeData) -> None:
    add_group_perm_to_user("test_group", user)
    add_group_perm_to_dataset("test_group", omni_dataset.study_id)
    assert user_has_permission("t4c8_instance", user, omni_dataset.study_id)


def test_dataset_group_rights_gives_access_to_all_descendants(
    user: User, omni_dataset: GenotypeData,
) -> None:
    add_group_perm_to_user("test_group", user)
    add_group_perm_to_dataset("test_group", omni_dataset.study_id)
    assert user_has_permission("t4c8_instance", user, "dataset_1")
    assert user_has_permission("t4c8_instance", user, "dataset_2")
    assert user_has_permission("t4c8_instance", user, "t4c8_study_1")
    assert user_has_permission("t4c8_instance", user, "t4c8_study_2")


def test_dataset_group_rights_gives_access_to_parent_dataset(
    user: User, omni_dataset: GenotypeData,
) -> None:
    add_group_perm_to_user("test_group", user)
    add_group_perm_to_dataset("test_group", "dataset_1")
    assert user_has_permission("t4c8_instance", user, omni_dataset.study_id)


def test_dataset_group_rights_mixed(
    user: User,
    custom_wgpf: GenotypeData,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    add_group_perm_to_user("test_group", user)
    add_group_perm_to_dataset("test_group", "dataset_1")
    assert user_has_permission("t4c8_instance", user, "t4c8_study_1")
    assert not user_has_permission("t4c8_instance", user, "t4c8_study_2")


def test_user_and_dataset_groups_getter_methods(
    user: User,
    custom_wgpf: GenotypeData,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    add_group_perm_to_user("test_group", user)
    add_group_perm_to_dataset("test_group", "omni_dataset")
    dataset = Dataset.objects.get(dataset_id="omni_dataset")
    assert get_user_groups(user) & get_dataset_groups(dataset)


def test_nauser_user_and_dataset_groups_getter_methods(
    na_user: User,
    custom_wgpf: GenotypeData,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    add_group_perm_to_user("test_group", na_user)
    add_group_perm_to_dataset("test_group", "omni_dataset")
    assert get_user_groups(na_user) & get_dataset_groups("omni_dataset")


@override_settings(DISABLE_PERMISSIONS=True)
def test_disable_permissions_flag_allows_all(
    na_user: User, omni_dataset: GenotypeData,
) -> None:
    data_ids = {*omni_dataset.get_studies_ids(),
                *omni_dataset.get_studies_ids(leaves=False)}
    for data_id in data_ids:
        assert user_has_permission("t4c8_instance", na_user, data_id)
