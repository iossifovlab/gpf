import logging

from rest_framework import permissions

from gpf_instance.gpf_instance import get_gpf_instance
from .models import Dataset
from utils.datasets import find_dataset_id_in_request
from guardian.utils import get_anonymous_user
from guardian.shortcuts import get_groups_with_perms
from django.contrib.auth.models import Group
from guardian.shortcuts import assign_perm


logger = logging.getLogger(__name__)


class IsDatasetAllowed(permissions.BasePermission):
    def has_permission(self, request, view):
        dataset_id = find_dataset_id_in_request(request)

        if dataset_id is None:
            return True

        return self.has_object_permission(request, view, dataset_id)

    def has_object_permission(self, request, view, dataset_id):
        if not user_has_permission(request.user, dataset_id):
            if not Dataset.objects.filter(dataset_id=dataset_id).exists():
                return False
            dataset_object = Dataset.objects.get(dataset_id=dataset_id)
            for group in get_groups_with_perms(dataset_object):
                if Dataset.objects.filter(dataset_id=group.name).exists():
                    if user_has_permission(request.user, group.name):
                        return True
            return False
        return True

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


def user_has_permission_strict(user, dataset_id):
    try:
        dataset = Dataset.objects.get(dataset_id=dataset_id)
    except Dataset.DoesNotExist:
        logger.warning(f"dataset {dataset_id} does not exists...")
        return False

    if get_anonymous_user().has_perm("datasets_api.view", dataset):
        return True
    if user.has_perm("datasets_api.view", dataset):
        return True

    return False


def user_has_permission(user, dataset_id):
    logger.debug(f"cheking access rights for dataset {dataset_id}")
    if user_has_permission_strict(user, dataset_id):
        return True

    gpf_instance = get_gpf_instance()
    genotype_data = gpf_instance.get_genotype_data(dataset_id)
    if genotype_data is None:
        return False
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
    return set(
        dataset_id for dataset_id in dataset_ids
        if user_has_permission_strict(user, dataset_id)
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
