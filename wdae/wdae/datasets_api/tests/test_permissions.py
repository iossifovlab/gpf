import pytest

from box import Box

from django.contrib.auth import get_user_model
from django.test import override_settings

from dae.studies.study import GenotypeDataGroup
from studies.study_wrapper import StudyWrapper
from datasets_api.models import Dataset
from datasets_api.permissions import user_has_permission, \
    add_group_perm_to_user, \
    add_group_perm_to_dataset, \
    _get_allowed_datasets_for_user, \
    get_allowed_genotype_studies, \
    get_user_groups, get_dataset_groups, \
    get_directly_allowed_genotype_data, \
    _user_has_permission_strict


@pytest.fixture()
def dataset_wrapper(request, db, wdae_gpf_instance):
    dataset1_wrapper = wdae_gpf_instance.get_wdae_wrapper("Dataset1")
    assert dataset1_wrapper is not None
    assert dataset1_wrapper.is_group

    dataset2_wrapper = wdae_gpf_instance.get_wdae_wrapper("Dataset2")
    assert dataset2_wrapper is not None
    assert dataset2_wrapper.is_group

    ds_config = Box(dataset1_wrapper.config.to_dict())
    ds_config.studies = (
        "Dataset1",
        "Dataset2",
    )
    ds_config.id = "Dataset"

    dataset = GenotypeDataGroup(
        ds_config,
        [
            dataset1_wrapper.genotype_data_study,
            dataset2_wrapper.genotype_data_study,
        ])
    assert dataset is not None
    assert dataset.study_id == "Dataset"

    dataset_wrapper = StudyWrapper(dataset, None, None)
    assert dataset_wrapper is not None
    assert dataset_wrapper.is_group

    Dataset.recreate_dataset_perm("Dataset")

    wdae_gpf_instance.register_genotype_data(dataset)

    # wdae_gpf_instance\
    #     ._variants_db\
    #     ._genotype_data_group_wrapper_cache["Dataset"] = dataset_wrapper
    # wdae_gpf_instance\
    #     ._variants_db\
    #     .genotype_data_group_configs["Dataset"] = ds_config

    assert "Dataset" in wdae_gpf_instance.get_genotype_data_ids()
    assert wdae_gpf_instance.get_genotype_data("Dataset") is not None

    def fin():
        wdae_gpf_instance.unregister_genotype_data(dataset)

    request.addfinalizer(fin)

    return dataset_wrapper


def test_parents(admin_client, wdae_gpf_instance, dataset_wrapper):
    assert dataset_wrapper.parents == set()

    dataset1 = wdae_gpf_instance.get_genotype_data("Dataset1")
    assert dataset1.parents == set(["Dataset"])

    dataset2 = wdae_gpf_instance.get_genotype_data("Dataset2")
    assert "Dataset" in dataset2.parents

    study1 = wdae_gpf_instance.get_genotype_data("Study1")
    assert "Dataset1" in study1.parents

    study2 = wdae_gpf_instance.get_genotype_data("Study2")
    assert "Dataset2" in study2.parents

    study3 = wdae_gpf_instance.get_genotype_data("Study3")
    assert "Dataset1" in study3.parents


def test_datasets_studies_ids(
        admin_client, wdae_gpf_instance, dataset_wrapper):

    study_ids = dataset_wrapper.get_studies_ids()
    assert set(study_ids) == set(["Study1", "Study2", "Study3"])

    study_ids = dataset_wrapper.get_studies_ids(leaves=False)
    assert set(study_ids) == set(["Dataset1", "Dataset2"])


def test_dataset_rights(db, user, dataset_wrapper):
    add_group_perm_to_user(dataset_wrapper.study_id, user)
    assert user_has_permission(user, dataset_wrapper.study_id)


def test_dataset1_rights(db, user, dataset_wrapper):
    add_group_perm_to_user("Dataset1", user)
    assert user_has_permission(user, dataset_wrapper.study_id)


def test_dataset1_rights_allowed_datasets(db, user, dataset_wrapper):
    add_group_perm_to_user("Dataset1", user)
    result = _get_allowed_datasets_for_user(
        user, dataset_wrapper.study_id)
    assert result == set(["Dataset1"])

    result = get_allowed_genotype_studies(
        user, dataset_wrapper.study_id)
    assert result == set(["Study1", "Study3"])


def test_dataset2_rights_allowed_datasets(db, user, dataset_wrapper):
    add_group_perm_to_user("Dataset2", user)
    result = _get_allowed_datasets_for_user(
        user, dataset_wrapper.study_id)
    assert result == set(["Dataset2"])

    result = get_allowed_genotype_studies(
        user, dataset_wrapper.study_id)
    assert result == set(["Study2"])


def test_study1_and_dataset2_rights_allowed_datasets(
        db, user, dataset_wrapper):

    add_group_perm_to_user("Dataset2", user)
    add_group_perm_to_user("Study1", user)

    result = _get_allowed_datasets_for_user(
        user, dataset_wrapper.study_id)
    assert result == set(["Study1", "Dataset2"])

    result = get_allowed_genotype_studies(
        user, dataset_wrapper.study_id)
    assert result == set(["Study1", "Study2"])


def test_dataset_group_rights(db, user, dataset_wrapper):
    add_group_perm_to_user("A", user)
    add_group_perm_to_dataset("A", dataset_wrapper.study_id)

    assert user_has_permission(user, dataset_wrapper.study_id)


def test_dataset_group_rights_gives_access_to_all_studies(
        db, user, dataset_wrapper):
    add_group_perm_to_user("A", user)
    add_group_perm_to_dataset("A", dataset_wrapper.study_id)

    assert user_has_permission(user, "Study1")
    assert user_has_permission(user, "Study2")
    assert user_has_permission(user, "Study3")


def test_dataset_group_rights_gives_access_to_all_datasets(
        db, user, dataset_wrapper):
    add_group_perm_to_user("A", user)
    add_group_perm_to_dataset("A", dataset_wrapper.study_id)

    assert user_has_permission(user, "Dataset1")
    assert user_has_permission(user, "Dataset2")
    assert user_has_permission(user, "Dataset")


def test_dataset1_group_rights(db, user, dataset_wrapper):
    add_group_perm_to_user("A", user)
    add_group_perm_to_dataset("A", "Dataset1")

    assert user_has_permission(user, dataset_wrapper.study_id)


def test_dataset1_group_rights_gives_access_to_study1_and_study3(
        db, user, dataset_wrapper):
    add_group_perm_to_user("A", user)
    add_group_perm_to_dataset("A", "Dataset1")

    assert user_has_permission(user, "Study1")
    assert user_has_permission(user, "Study3")

    assert not user_has_permission(user, "Study2")


def test_study1_and_dataset2_group_rights_allowed_datasets(
        db, user, dataset_wrapper):

    add_group_perm_to_user("A", user)
    add_group_perm_to_dataset("A", "Dataset2")
    add_group_perm_to_dataset("A", "Study1")

    result = _get_allowed_datasets_for_user(
        user, dataset_wrapper.study_id)
    assert result == set(["Study1", "Dataset2"])

    result = get_allowed_genotype_studies(
        user, dataset_wrapper.study_id)
    assert result == set(["Study1", "Study2"])


def test_dataset_any_dataset_group_rights(db, user, dataset_wrapper):
    add_group_perm_to_user("any_dataset", user)

    assert user_has_permission(user, dataset_wrapper.study_id)

    result = _get_allowed_datasets_for_user(
        user, dataset_wrapper.study_id)
    assert result == set(["Dataset"])

    result = get_allowed_genotype_studies(
        user, dataset_wrapper.study_id)
    assert result == set(["Study1", "Study2", "Study3"])


def test_dataset_admin_group_rights(db, user, dataset_wrapper):
    add_group_perm_to_user("admin", user)

    assert user_has_permission(user, dataset_wrapper.study_id)

    result = _get_allowed_datasets_for_user(
        user, dataset_wrapper.study_id)
    assert result == set(["Dataset"])

    result = get_allowed_genotype_studies(
        user, dataset_wrapper.study_id)
    assert result == set(["Study1", "Study2", "Study3"])


def test_explore_datasets_users_and_groups(db, user, dataset_wrapper):
    add_group_perm_to_user("A", user)
    add_group_perm_to_dataset("A", "Dataset")

    dataset = Dataset.objects.get(dataset_id="Dataset")

    assert get_user_groups(user) & get_dataset_groups(dataset)


@pytest.fixture()
def na_user(db):
    User = get_user_model()
    u = User.objects.create(
        email="nauser@example.com",
        name="Non-Active User",
        is_staff=False,
        is_active=False,
        is_superuser=False,
    )
    u.save()

    return u


def test_explore_datasets_nauser_and_groups(db, na_user, dataset_wrapper):
    add_group_perm_to_user("A", na_user)
    add_group_perm_to_dataset("A", "Dataset")

    print(get_user_groups(na_user))
    print(get_dataset_groups("Dataset"))

    assert get_user_groups(na_user) & get_dataset_groups("Dataset")


def test_get_allowed_datasets_for_na_user_strict(db, na_user, dataset_wrapper):
    add_group_perm_to_user("A", na_user)
    add_group_perm_to_dataset("A", "Dataset")

    allowed_dtasets = get_directly_allowed_genotype_data(na_user)
    print(allowed_dtasets)
    assert "Dataset" in allowed_dtasets
    assert not _user_has_permission_strict(na_user, "Dataset")


def test_get_directly_allowed_genotype_data(db, user, dataset_wrapper):
    add_group_perm_to_user("A", user)
    add_group_perm_to_dataset("A", "Dataset")

    allowed_dtasets = get_directly_allowed_genotype_data(user)
    print(allowed_dtasets)
    assert "Dataset" in allowed_dtasets
    assert _user_has_permission_strict(user, "Dataset")


def test_get_allowed_dataset_from_parent(db, user, dataset_wrapper):
    add_group_perm_to_user("A", user)
    add_group_perm_to_dataset("A", "Dataset")

    allowed_datasets = _get_allowed_datasets_for_user(user, "Dataset1")
    assert "Dataset1" in allowed_datasets


@override_settings(DISABLE_PERMISSIONS=True)
def test_disable_permissions_flag_allows_all(db, na_user, dataset_wrapper):
    data_ids = {*dataset_wrapper.get_studies_ids(),
                *dataset_wrapper.get_studies_ids(leaves=False)}
    for data_id in data_ids:
        assert user_has_permission(na_user, data_id)
