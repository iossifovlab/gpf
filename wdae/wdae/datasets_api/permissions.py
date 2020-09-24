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


def get_wdae_children(dataset):
    genotype_data = get_genotype_data(dataset)
    if genotype_data is None:
        return []
    return [
        get_wdae_dataset(sid)
        for sid in genotype_data.get_studies_ids(leafs=False)
    ]


def user_has_permission_strict(user, dataset):
    dataset = get_wdae_dataset(dataset)
    if dataset is None:
        return False

    user_groups = get_user_groups(user)
    dataset_groups = get_dataset_groups(dataset)
    if not (user_groups & dataset_groups):
        return False

    if get_anonymous_user().has_perm("datasets_api.view", dataset):
        return True

    return user.has_perm("datasets_api.view", dataset)


def _check_parents_permissions(user, genotype_data):
    gpf_instance = get_gpf_instance()

    for parent_id in genotype_data.parents:
        if user_has_permission_strict(user, parent_id):
            return True
        parent = gpf_instance.get_genotype_data(parent_id)
        if _check_parents_permissions(user, parent):
            return True


def user_has_permission(user, dataset):
    dataset = get_wdae_dataset(dataset)

    logger.debug(f"cheking access rights for dataset {dataset.dataset_id}")
    if user_has_permission_strict(user, dataset):
        return True

    gpf_instance = get_gpf_instance()
    genotype_data = gpf_instance.get_genotype_data(dataset.dataset_id)
    if genotype_data is None:
        return False

    if _check_parents_permissions(user, genotype_data):
        return True

    if not genotype_data.is_group:
        return False

    for study_id in genotype_data.get_studies_ids(leafs=False):
        if user_has_permission(user, study_id):
            return True

    return False


def user_allowed_datasets(user, dataset_id):
    if user_has_permission_strict(user, dataset_id):
        return set([dataset_id])
    gpf_instance = get_gpf_instance()
    genotype_data = gpf_instance.get_genotype_data(dataset_id)
    if genotype_data is None:
        return set([])
    if not genotype_data.is_group:
        return set([])

    result = []
    for study_id in genotype_data.get_studies_ids(leafs=False):
        result.extend(user_allowed_datasets(user, study_id))
    return set(result)


def get_allowed_datasets_for_user(user):
    gpf_instance = get_gpf_instance()
    dataset_ids = gpf_instance.get_genotype_data_ids()
    user_groups = get_user_groups(user)

    return set(
        dataset_id for dataset_id in dataset_ids
        if user_groups & get_dataset_groups(dataset_id)
    )


def user_allowed_datasets_deep(user, dataset_id):
    datasets = user_allowed_datasets(user, dataset_id)
    gpf_instance = get_gpf_instance()

    result = []
    for dataset_id in datasets:
        genotype_data = gpf_instance.get_genotype_data(dataset_id)
        result.extend(genotype_data.get_studies_ids(leafs=True))
    return set(result)


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
