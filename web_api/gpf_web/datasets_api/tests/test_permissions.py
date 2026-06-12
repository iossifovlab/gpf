# pylint: disable=W0621,C0114,C0116,W0212,W0613,C0415,
from typing import cast
from unittest.mock import patch

import pytest
from box import Box
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, User
from django.test import override_settings
from gpf_instance.gpf_instance import WGPFInstance
from studies.study_wrapper import WDAEStudy

from datasets_api.models import Dataset
from datasets_api.permissions import (
    IsDatasetAllowed,
    add_group_perm_to_dataset,
    add_group_perm_to_user,
    get_dataset_groups,
    get_user_groups,
    remove_group_perm_from_dataset,
    user_has_permission,
)
from gpf.studies.study import GenotypeData, GenotypeDataGroup


@pytest.fixture
def omni_dataset(custom_wgpf: WGPFInstance) -> GenotypeData:
    """Easy-access fixture for the dataset containing all genotype data."""
    return custom_wgpf.get_genotype_data("omni_dataset")


@pytest.fixture
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


def _reload_user(user: User) -> User:
    """Re-fetch a user from the DB as a fresh instance.

    Simulates a new request: ``request.user`` is built fresh per request, so
    the request-scoped ``permitted_datasets`` memo never survives a permission
    mutation in production. Tests that mutate permissions and re-check on the
    same Python object must reload to model that boundary.
    """
    return cast(User, get_user_model().objects.get(pk=user.pk))


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
    assert not user_has_permission(
        "t4c8_instance", user, omni_dataset.study_id)
    add_group_perm_to_user(omni_dataset.study_id, user)
    user = _reload_user(user)  # new request: fresh memo
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


def test_any_user_propagates_to_parents(
    omni_dataset: GenotypeData,
) -> None:
    add_group_perm_to_dataset("any_user", "dataset_1")
    assert user_has_permission("t4c8_instance",
                               cast(User, AnonymousUser()),
                               omni_dataset.study_id)


def test_any_user_propagates_to_children(
    omni_dataset: GenotypeData,
) -> None:
    add_group_perm_to_dataset("any_user", omni_dataset.study_id)
    assert user_has_permission("t4c8_instance",
                               cast(User, AnonymousUser()),
                               "dataset_1")


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


def test_unregistered_dataset_does_not_propagate_permissions(
    custom_wgpf: WGPFInstance,
) -> None:
    """
    Test for faulty permissions propagations.
    Permissions were changed to return True for missing datasets, which
    resulted in a bug where checking parent/child permissions would return
    True when it shouldn't when a parent dataset suddenly disappears.
    """
    dataset1_wrapper = custom_wgpf.get_wdae_wrapper("dataset_1")
    assert dataset1_wrapper is not None
    assert dataset1_wrapper.genotype_data.is_group

    dataset2_wrapper = custom_wgpf.get_wdae_wrapper("dataset_2")
    assert dataset2_wrapper is not None
    assert dataset2_wrapper.genotype_data.is_group

    ds_config = Box(dataset1_wrapper.genotype_data.config)
    ds_config.studies = ("dataset_1", "dataset_2")
    ds_config.id = "big_dataset"

    dataset = GenotypeDataGroup(
        custom_wgpf.genotype_storages,
        ds_config, [dataset1_wrapper.genotype_data,
                    dataset2_wrapper.genotype_data],
    )
    assert dataset is not None
    assert dataset.study_id == "big_dataset"

    dataset_wrapper = WDAEStudy(custom_wgpf.genotype_storages, dataset, None)
    assert dataset_wrapper is not None
    assert dataset_wrapper.is_group

    Dataset.recreate_dataset_perm("big_dataset")

    custom_wgpf._variants_db.register_genotype_data(dataset)

    assert "big_dataset" in custom_wgpf.get_genotype_data_ids()
    assert custom_wgpf.get_genotype_data("big_dataset") is not None

    custom_wgpf._variants_db.unregister_genotype_data(dataset)
    custom_wgpf.get_genotype_data("dataset_1")._parents = set()
    custom_wgpf.get_genotype_data("dataset_2")._parents = set()

    study1 = custom_wgpf.get_genotype_data("t4c8_study_1")
    assert study1 is not None

    assert not user_has_permission(
        "t4c8_instance",
        cast(User, AnonymousUser()),
        study1.study_id,
    )


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


def test_any_user_with_anonymous(omni_dataset: GenotypeData) -> None:
    anonymous_user = cast(User, AnonymousUser())
    assert not user_has_permission("t4c8_instance", anonymous_user,
                                   omni_dataset.study_id)
    add_group_perm_to_dataset("any_user", "omni_dataset")
    assert user_has_permission("t4c8_instance", anonymous_user,
                               omni_dataset.study_id)


def test_permitted_datasets_cte_runs_once_per_user(
    user: User,
    custom_wgpf: GenotypeData,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    """Within one request (same user instance) the CTE runs once.

    Tracer bullet for gpf#926: a request-scoped memo on the user object
    means two calls to ``permitted_datasets`` for the same user+instance
    execute the expensive recursive CTE only once.
    """
    add_group_perm_to_user("test_group", user)
    add_group_perm_to_dataset("test_group", "dataset_1")

    with patch.object(
        IsDatasetAllowed,
        "prepare_allowed_datasets_query",
        wraps=IsDatasetAllowed.prepare_allowed_datasets_query,
    ) as spy:
        first = set(IsDatasetAllowed.permitted_datasets(user, "t4c8_instance"))
        second = set(IsDatasetAllowed.permitted_datasets(user, "t4c8_instance"))

    assert spy.call_count == 1
    assert first == second
    assert "dataset_1" in first


def test_permitted_datasets_memo_is_correct(
    user: User,
    custom_wgpf: GenotypeData,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    """The memoized result equals a freshly-computed permitted set."""
    add_group_perm_to_user("test_group", user)
    add_group_perm_to_dataset("test_group", "dataset_1")

    fresh = set(IsDatasetAllowed.permitted_datasets(user, "t4c8_instance"))
    cached = set(IsDatasetAllowed.permitted_datasets(user, "t4c8_instance"))
    assert cached == fresh
    # all real permitted-via-hierarchy datasets present
    assert {"dataset_1", "omni_dataset",
            "t4c8_study_1"}.issubset(cached)
    assert "t4c8_study_2" not in cached


def test_permitted_datasets_no_cross_request_leak(
    custom_wgpf: GenotypeData,  # noqa: ARG001 ; setup WGPF instance
    db: None,  # noqa: ARG001
) -> None:
    """A different user object (new request) recomputes independently.

    Guards against accidental process-global caching: the memo must live
    on the per-request ``request.user`` instance, not be shared across
    requests/users.
    """
    user_model = get_user_model()
    user_a = cast(User, user_model.objects.create(
        email="a@example.com", name="A",
        is_staff=False, is_active=True, is_superuser=False,
    ))
    user_a.save()
    add_group_perm_to_user("test_group", user_a)
    add_group_perm_to_dataset("test_group", "dataset_1")

    user_b = cast(User, user_model.objects.create(
        email="b@example.com", name="B",
        is_staff=False, is_active=True, is_superuser=False,
    ))
    user_b.save()
    # user_b has no permissions

    a_sets = set(IsDatasetAllowed.permitted_datasets(user_a, "t4c8_instance"))
    assert "dataset_1" in a_sets

    # Re-fetch user_a from the DB -> a brand new instance, like a new
    # request. Its memo must be empty and recompute independently.
    user_a_reloaded = cast(User, user_model.objects.get(email="a@example.com"))
    with patch.object(
        IsDatasetAllowed,
        "prepare_allowed_datasets_query",
        wraps=IsDatasetAllowed.prepare_allowed_datasets_query,
    ) as spy:
        reloaded_sets = set(
            IsDatasetAllowed.permitted_datasets(
                user_a_reloaded, "t4c8_instance"))
    assert spy.call_count == 1
    assert reloaded_sets == a_sets

    # A different user must not read user_a's cached value.
    b_sets = set(IsDatasetAllowed.permitted_datasets(user_b, "t4c8_instance"))
    assert "dataset_1" not in b_sets


def test_permitted_datasets_memo_keyed_per_instance(
    user: User,
    custom_wgpf: GenotypeData,  # noqa: ARG001 ; setup WGPF instance
) -> None:
    """The per-user memo is keyed by ``instance_id`` and does not collide.

    The same user object querying two different instance IDs must get
    independent results -- a hit for one instance must not be returned for
    another. ``t4c8_instance`` has permitted datasets; an unknown instance
    has none.
    """
    add_group_perm_to_user("test_group", user)
    add_group_perm_to_dataset("test_group", "dataset_1")

    real = set(IsDatasetAllowed.permitted_datasets(user, "t4c8_instance"))
    assert "dataset_1" in real

    # A second instance_id on the same (now-populated) user object must not
    # collide with the cached entry for "t4c8_instance".
    other = set(IsDatasetAllowed.permitted_datasets(user, "other_instance"))
    assert other == set()

    # And the first instance's cached value is unchanged.
    real_again = set(
        IsDatasetAllowed.permitted_datasets(user, "t4c8_instance"))
    assert real_again == real


def test_user_group_permissions(
    user: User,
    omni_dataset: GenotypeData,
) -> None:
    assert not user_has_permission(
        "t4c8_instance", user, omni_dataset.study_id)

    add_group_perm_to_dataset(
        user.email, omni_dataset.study_id)

    user = _reload_user(user)  # new request: fresh memo
    assert user_has_permission("t4c8_instance", user, omni_dataset.study_id)

    remove_group_perm_from_dataset(
        user.email, omni_dataset.study_id,
    )

    user = _reload_user(user)  # new request: fresh memo
    assert not user_has_permission(
        "t4c8_instance", user, omni_dataset.study_id)
