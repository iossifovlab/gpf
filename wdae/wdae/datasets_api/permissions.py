import logging

from rest_framework import permissions

from gpf_instance.gpf_instance import get_gpf_instance
from .models import Dataset
from utils.datasets import find_dataset_id_in_request
from dae.studies.study import GenotypeData

from django.contrib.auth.models import Group
from django.utils.encoding import force_str

from guardian.utils import get_anonymous_user
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

        if not Dataset.objects.filter(dataset_id=dataset_id).exists():
            return False
        dataset_object = Dataset.objects.get(dataset_id=dataset_id)
        for group in get_groups_with_perms(dataset_object):
            if Dataset.objects.filter(dataset_id=group.name).exists():
                if user_has_permission(request.user, group.name):
                    return True
        return False

    @staticmethod
    def permitted_datasets(user):
        dataset_ids = get_gpf_instance().get_genotype_data_ids()

        return list(
            filter(
                lambda dataset_id: user_has_permission_strict(
                    user, dataset_id
                ),
                dataset_ids,
            )
        )


def get_wdae_dataset(dataset):
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
    if isinstance(dataset, GenotypeData):
        return dataset

    if isinstance(dataset, Dataset):
        dataset_id = dataset.dataset_id
    else:
        dataset_id = force_str(dataset)

    gpf_instance = get_gpf_instance()
    return gpf_instance.get_genotype_data(dataset_id)


def get_wdae_parents(dataset):
    genotype_data = get_genotype_data(dataset)
    if genotype_data is None:
        return []
    return [get_wdae_dataset(pid) for pid in genotype_data.parents]


def get_wdae_children(dataset, leafs=False):
    genotype_data = get_genotype_data(dataset)
    if genotype_data is None:
        return []

    if not genotype_data.is_group:
        return []

    return [
        get_wdae_dataset(sid)
        for sid in genotype_data.get_studies_ids(leafs=leafs)
    ]


def user_has_permission_strict(user, dataset):
    dataset = get_wdae_dataset(dataset)
    if dataset is None:
        return False

    if user.is_superuser or user.is_staff:
        return True

    user_groups = get_user_groups(user)
    if "admin" in user_groups:
        return True

    dataset_groups = get_dataset_groups(dataset)
    if not (user_groups & dataset_groups):
        return False

    if get_anonymous_user().has_perm("datasets_api.view", dataset):
        return True

    return user.has_perm("datasets_api.view", dataset)


def user_has_permission_up(user, dataset):
    dataset = get_wdae_dataset(dataset)
    if dataset is None:
        return False

    if user_has_permission_strict(user, dataset):
        return True

    for parent in get_wdae_parents(dataset):
        if user_has_permission_strict(user, parent):
            return True
        if user_has_permission_up(user, parent):
            return True
    return False


def user_has_permission_down(user, dataset):
    dataset = get_wdae_dataset(dataset)
    if dataset is None:
        return False

    for child in get_wdae_children(dataset):
        if user_has_permission_strict(user, child):
            return True
        if user_has_permission_down(user, child):
            return True
    return False


def user_has_permission(user, dataset):
    logger.debug(f"checking user <{user}> permissions on {dataset}")
    dataset = get_wdae_dataset(dataset)
    if dataset is None:
        return False

    allowed_dataset_leafs = get_allowed_datasets_leafs_for_user(user, dataset)
    return bool(allowed_dataset_leafs)

    # logger.debug(f"cheking access rights for dataset {dataset.dataset_id}")
    # if user_has_permission_strict(user, dataset):
    #     return True

    # if user_has_permission_up(user, dataset):
    #     return True
    # if user_has_permission_down(user, dataset):
    #     return True

    # return False


def get_allowed_datasets_for_user(user, dataset, collect=None):

    if collect is None:
        collect = set()

    dataset = get_wdae_dataset(dataset)
    if dataset is None:
        return collect

    if user_has_permission_up(user, dataset):
        collect.add(dataset.dataset_id)
        return collect

    for child in get_wdae_children(dataset):
        if user_has_permission_strict(user, child):
            collect.add(child.dataset_id)
        else:
            result = get_allowed_datasets_for_user(user, child)
            collect = collect | result
    return collect


def get_allowed_datasets_leafs_for_user(user, dataset):
    allowed_datasets = get_allowed_datasets_for_user(user, dataset)

    result = []
    for dataset in allowed_datasets:
        children = get_wdae_children(dataset, leafs=True)
        if not children:
            result.append(dataset)
        result.extend([child.dataset_id for child in children])
    return set(result)


def get_all_allowed_datasets_for_user(user):
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
