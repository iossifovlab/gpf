import logging

from rest_framework import permissions

from gpf_instance.gpf_instance import get_gpf_instance
from .models import Dataset
from utils.datasets import find_dataset_id_in_request
from dae.studies.study import GenotypeData

from django.contrib.auth.models import Group
from django.utils.encoding import force_str

from guardian.shortcuts import get_groups_with_perms
from guardian.shortcuts import assign_perm


logger = logging.getLogger(__name__)


class IsDatasetAllowed(permissions.BasePermission):
    def has_permission(self, request, view):
        dataset_id = find_dataset_id_in_request(request)

        if dataset_id is None:
            return True

        return self.has_object_permission(request, view, dataset_id)

    def has_object_permission(self, request, view, dataset_id):
        if user_has_permission(request.user, dataset_id):
            return True

        return False

    @staticmethod
    def permitted_datasets(user):
        dataset_ids = get_gpf_instance().get_genotype_data_ids()

        return list(
            filter(
                lambda dataset_id: _user_has_permission_strict(
                    user, dataset_id
                ),
                dataset_ids,
            )
        )


def get_wdae_dataset(dataset):
    """Given a dataset ID or DAE genotype data object, returns WDAE dataset
    object"""
    if isinstance(dataset, Dataset):
        return dataset
    elif isinstance(dataset, GenotypeData):
        dataset_id = dataset.id
    else:
        dataset_id = force_str(dataset)

    if not Dataset.objects.filter(dataset_id=dataset_id).exists():
        logger.warning(f"dataset {dataset_id} does not exists...")
        return None
    return Dataset.objects.get(dataset_id=dataset_id)


def get_genotype_data(dataset):
    """Given a dataset ID or WDAE dataset object, returns DAE genotype data
    object"""
    if isinstance(dataset, GenotypeData):
        return dataset

    if isinstance(dataset, Dataset):
        dataset_id = dataset.dataset_id
    else:
        dataset_id = force_str(dataset)

    gpf_instance = get_gpf_instance()
    return gpf_instance.get_genotype_data(dataset_id)


def get_wdae_parents(dataset):
    """Given a dataset ID or DAE genotype data object or WDAE dataset object,
    returns list of parents as WDAE dataset object"""
    genotype_data = get_genotype_data(dataset)
    if genotype_data is None:
        return []
    return [get_wdae_dataset(pid) for pid in genotype_data.parents]


def get_wdae_children(dataset, leafs=False):
    """Given a dataset ID or DAE genotype data object or WDAE dataset object,
    returns list of direct childrens as WDAE dataset object (if 'leafs'
    parameter is 'False'). If 'leafs' parameter is 'True', returns list
    of leafs of the datasets tree."""
    genotype_data = get_genotype_data(dataset)
    if genotype_data is None:
        return []

    if not genotype_data.is_group:
        return []

    return [
        get_wdae_dataset(sid)
        for sid in genotype_data.get_studies_ids(leafs=leafs)
    ]


def _user_has_permission_strict(user, dataset):
    "Checks if a user has access strictly to the given datasets"

    dataset = get_wdae_dataset(dataset)
    if dataset is None:
        return False

    if user.is_superuser or user.is_staff:
        return True

    # if get_anonymous_user().has_perm("datasets_api.view", dataset):
    #     return True

    user_groups = get_user_groups(user)
    if "admin" in user_groups:
        return True

    dataset_groups = get_dataset_groups(dataset)
    if 'any_user' in dataset_groups:
        return True

    if not bool(user_groups & dataset_groups):
        return False

    return user.has_perm("datasets_api.view", dataset)


def _user_has_permission_up(user, dataset):
    """Checks if a user has access strictly to the given datasets or to any
    of the dataset parents
    """

    dataset = get_wdae_dataset(dataset)
    if dataset is None:
        return False

    if _user_has_permission_strict(user, dataset):
        return True

    for parent in get_wdae_parents(dataset):
        if _user_has_permission_strict(user, parent):
            return True
        if _user_has_permission_up(user, parent):
            return True
    return False


def _user_has_permission_down(user, dataset):
    """Checks if a user has access strictly to the given datasets or to any
    of the dataset children.
    """

    dataset = get_wdae_dataset(dataset)
    if dataset is None:
        return False

    if _user_has_permission_strict(user, dataset):
        return True

    for child in get_wdae_children(dataset):
        if _user_has_permission_strict(user, child):
            return True
        if _user_has_permission_down(user, child):
            return True
    return False


def user_has_permission(user, dataset):
    """Checks if a user has permission to browse the given dataset"""

    logger.debug(f"checking user <{user}> permissions on {dataset}")
    dataset = get_wdae_dataset(dataset)
    if dataset is None:
        return False

    allowed_dataset_leafs = get_allowed_genotype_studies(user, dataset)
    return bool(allowed_dataset_leafs)


def _get_allowed_datasets_for_user(user, dataset, collect=None):
    """Walks through the dataset's hierarcy sub-tree starting with the given
    `dataset` and collects earliest in the hierarchy datasets IDs the user
    has access to."""

    if collect is None:
        collect = set()

    dataset = get_wdae_dataset(dataset)
    if dataset is None:
        return collect

    if _user_has_permission_up(user, dataset):
        collect.add(dataset.dataset_id)
        return collect

    for child in get_wdae_children(dataset):
        if _user_has_permission_strict(user, child):
            collect.add(child.dataset_id)
        else:
            result = _get_allowed_datasets_for_user(user, child)
            collect = collect | result
    return collect


def get_allowed_genotype_studies(user, dataset):
    """Finds the leafs of the dataset sub-tree with root `dataset`,
    such that user has access to and returns a set of dataset IDs
    of those datasets."""

    allowed_datasets = _get_allowed_datasets_for_user(user, dataset)

    result = []
    for dataset in allowed_datasets:
        children = get_wdae_children(dataset, leafs=True)
        if not children:
            result.append(dataset)
        result.extend([child.dataset_id for child in children])
    return set(result)


def get_directly_allowed_genotype_data(user):
    gpf_instance = get_gpf_instance()
    dataset_ids = gpf_instance.get_genotype_data_ids()
    user_groups = get_user_groups(user)

    return set(
        dataset_id for dataset_id in dataset_ids
        if user_groups & get_dataset_groups(dataset_id)
    )


def add_group_perm_to_user(group_name, user):
    group, _created = Group.objects.get_or_create(name=group_name)

    user.groups.add(group)
    user.save()


def add_group_perm_to_dataset(group_name, dataset_id):
    dataset, _created = Dataset.objects.get_or_create(dataset_id=dataset_id)
    group, _created = Group.objects.get_or_create(name=group_name)
    assign_perm("view", group, dataset)


def get_user_groups(user):
    return {g.name for g in user.groups.all()}


def get_dataset_groups(dataset):
    if not isinstance(dataset, Dataset):
        dataset = Dataset.objects.get(dataset_id=force_str(dataset))
    return {g.name for g in get_groups_with_perms(dataset)}
