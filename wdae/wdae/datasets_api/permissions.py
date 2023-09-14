import logging

from typing import Any, Optional, List, cast
from rest_framework import permissions

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.utils.encoding import force_str
from django.http import HttpRequest

from gpf_instance.gpf_instance import get_wgpf_instance
from utils.datasets import find_dataset_id_in_request

from .models import Dataset, DatasetHierarchy


logger = logging.getLogger(__name__)


class IsDatasetAllowed(permissions.BasePermission):
    """Checks the permissions to a dataset."""

    def has_permission(self, request: HttpRequest, view: Any) -> bool:
        dataset_id = find_dataset_id_in_request(request)

        if dataset_id is None:
            return True

        return self.has_object_permission(request, view, dataset_id)

    def has_object_permission(
            self, request: HttpRequest, view: Any, obj: str
    ) -> bool:
        if user_has_permission(cast(User, request.user), obj):
            return True

        return False

    @staticmethod
    def permitted_datasets(user: User) -> list[str]:
        dataset_ids = get_wgpf_instance().get_genotype_data_ids()

        return list(
            filter(
                lambda dataset_id: user_has_permission(
                    user, dataset_id
                ),
                dataset_ids,
            )
        )


def get_wdae_dataset(
    dataset: str
) -> Optional[Dataset]:
    """
    Return wdae dataset object.

    Given a dataset ID or DAE genotype data object, returns WDAE dataset
    object.
    """
    dataset_id = force_str(dataset)
    # pylint: disable=no-member
    if not Dataset.objects.filter(dataset_id=dataset_id).exists():
        logger.warning("dataset %s does not exists...", dataset_id)
        return None
    return Dataset.objects.get(dataset_id=dataset_id)


def get_wdae_parents(dataset_id: str, direct: bool = False) -> List[Dataset]:
    """
    Return list of parent wdae dataset objects.

    Given a dataset ID or DAE genotype data object or WDAE dataset object,
    returns list of parents as WDAE dataset object.
    """
    dataset = get_wdae_dataset(dataset_id)
    if dataset is None:
        return []
    if direct:
        return DatasetHierarchy.get_parents(dataset, True)

    return DatasetHierarchy.get_parents(dataset)


def get_wdae_children(dataset_id: str) -> List[Dataset]:
    """
    Return list of child wdae dataset objects.

    Given a dataset ID or DAE genotype data object or WDAE dataset object,
    returns list of direct childrens as WDAE dataset object (if 'leaves'
    parameter is 'False'). If 'leaves' parameter is 'True', returns list
    of leaves of the datasets tree.
    """
    dataset = get_wdae_dataset(dataset_id)
    if dataset is None:
        return []
    return DatasetHierarchy.get_children(dataset)


def _user_has_permission_strict(user: User, dataset_id: str) -> bool:
    """
    Check if a user has access strictly to the given dataset.

    None datasets will return True, as missing datasets should be the
    responsibility of the view to handle or return a 404 response.
    """
    if settings.DISABLE_PERMISSIONS:
        return True

    dataset = get_wdae_dataset(dataset_id)
    if dataset is None:
        return True

    dataset_groups = get_dataset_groups(dataset)

    if "any_user" in dataset_groups:
        return True

    if not user.is_active:
        return False

    if user.is_superuser or user.is_staff:
        return True

    user_groups = get_user_groups(user)
    if "admin" in user_groups:
        return True

    return bool(user_groups & dataset_groups)


def _user_has_permission_up(user: User, dataset_id: str) -> bool:
    """
    Check user permissions on a dataset's parents.

    Checks if a user has access to any of the dataset parents.
    """
    dataset = get_wdae_dataset(dataset_id)
    if dataset is None:
        return True

    for parent in get_wdae_parents(dataset.dataset_id):
        if parent is None:
            logger.error("%s has missing parent!", dataset.dataset_id)
            continue
        if _user_has_permission_strict(user, parent.dataset_id):
            return True
    return False


def _user_has_permission_down(user: User, dataset_id: str) -> bool:
    """
    Check user permissions on a dataset's children.

    Checks if a user has access to any of the dataset's children.
    """
    dataset = get_wdae_dataset(dataset_id)
    if dataset is None:
        return True

    for child in get_wdae_children(dataset.dataset_id):
        if child is None:
            logger.error("%s has missing parent!", dataset.dataset_id)
            continue
        if _user_has_permission_strict(user, child.dataset_id):
            return True
    return False


def user_has_permission(user: User, dataset_id: str) -> bool:
    """Check if a user has permission to browse the given dataset."""
    logger.debug("checking user <%s> permissions on %s", user, dataset_id)
    dataset = get_wdae_dataset(dataset_id)
    if dataset is None:
        return True

    if _user_has_permission_strict(user, dataset.dataset_id):
        return True
    if _user_has_permission_up(user, dataset.dataset_id):
        return True
    if _user_has_permission_down(user, dataset.dataset_id):
        return True

    return False


def get_allowed_genotype_studies(user: User, dataset_id: str) -> set[Dataset]:
    """Collect and return genotype study IDs the user has access to."""
    allowed_studies = []
    dataset = get_wdae_dataset(dataset_id)
    if dataset is None:
        return set()
    if DatasetHierarchy.is_study(dataset):
        if _user_has_permission_strict(user, dataset.dataset_id) \
                or _user_has_permission_up(user, dataset.dataset_id):
            allowed_studies.append(dataset.dataset_id)
    for child in get_wdae_children(dataset.dataset_id):
        if DatasetHierarchy.is_study(child):
            if _user_has_permission_strict(user, child.dataset_id) \
                    or _user_has_permission_up(user, child.dataset_id):
                allowed_studies.append(child.dataset_id)

    return set(allowed_studies)


def get_allowed_genotype_data(user: User, dataset_id: str) -> set[Dataset]:
    """Collect and return genotype data IDs the user has access to."""
    allowed_genotype_data = []
    dataset = get_wdae_dataset(dataset_id)
    if dataset is None:
        return set()
    for child in get_wdae_children(dataset.dataset_id):
        if _user_has_permission_strict(user, child.dataset_id) \
                or _user_has_permission_up(user, child.dataset_id):
            allowed_genotype_data.append(child.dataset_id)
    if len(allowed_genotype_data) > 0:
        allowed_genotype_data.append(dataset.dataset_id)
    return set(allowed_genotype_data)


def get_dataset_info(dataset_id: str) -> Optional[dict[str, Any]]:
    """Return a dictionary describing a Dataset object."""
    dataset = get_wdae_dataset(dataset_id)
    if dataset is None:
        logger.error("Could not find WDAE dataset for %s", dataset_id)
        return None
    return {
        "datasetName": dataset.dataset_name,
        "datasetId": dataset.dataset_id,
        "broken": dataset.broken
    }


def get_directly_allowed_genotype_data(user: User) -> list[dict[str, Any]]:
    """Return list of genotype data the user has direct permissions to."""
    gpf_instance = get_wgpf_instance()
    dataset_ids = gpf_instance.get_genotype_data_ids()
    user_groups = get_user_groups(user)
    datasets = {
        dataset.dataset_id: dataset
        for dataset in Dataset.objects.all()  # pylint: disable=no-member
    }

    result = []

    for dataset_id in dataset_ids:
        if dataset_id not in datasets:
            logger.warning(
                "Dataset %s found in DAE, but not in WDAE!", dataset_id
            )
            result.append({
                "datasetName": dataset_id,
                "datasetId": dataset_id,
                "broken": True
            })

        dataset = datasets[dataset_id]
        if not user_groups & get_dataset_groups(dataset):
            continue

        dataset_info = get_dataset_info(dataset_id)
        if dataset_info is not None:
            result.append(dataset_info)

    return sorted(
        result,
        key=lambda ds: ds["datasetName"] if ds["datasetName"] is not None
        else ds["datasetId"]

    )


def add_group_perm_to_user(group_name: str, user: User) -> None:
    group, _created = Group.objects.get_or_create(name=group_name)

    user.groups.add(group)
    user.save()


def add_group_perm_to_dataset(group_name: str, dataset_id: str) -> None:
    # pylint: disable=no-member
    dataset, _created = Dataset.objects.get_or_create(dataset_id=dataset_id)
    group, _created = Group.objects.get_or_create(name=group_name)
    dataset.groups.add(group)


def get_user_groups(user: User) -> set[str]:
    return {g.name for g in user.groups.all()}


def get_dataset_groups(dataset: Dataset) -> set[str]:
    # pylint: disable=no-member
    if not isinstance(dataset, Dataset):
        dataset = Dataset.objects.get(dataset_id=force_str(dataset))
    return {g.name for g in dataset.groups.all()}


def handle_partial_permissions(
    user: User, dataset_id: str, request_data: dict
) -> None:
    """Handle partial permission on a dataset.

    A user may have only partial access to a dataset based
    on which of its constituent studies he has rights to access.
    This method attaches these rights to the request as study filters
    in order to filter variants from studies the user cannot access.
    """
    request_data["allowed_studies"] = \
        get_allowed_genotype_studies(user, dataset_id)
