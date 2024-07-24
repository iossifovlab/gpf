import hashlib
import logging
import textwrap
from collections.abc import Iterable
from typing import Any, cast

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.db import connection
from django.http import HttpRequest
from django.utils.encoding import force_str
from gpf_instance.gpf_instance import (
    get_instance_timestamp,
    get_permission_timestamp,
    get_wgpf_instance,
)
from rest_framework import permissions
from rest_framework.request import Request
from utils.datasets import find_dataset_id_in_request

from .models import Dataset, DatasetHierarchy

logger = logging.getLogger(__name__)


def get_instance_timestamp_etag(
    _request: Request, **_kwargs: dict[str, Any],
) -> str:
    etag = f"{get_instance_timestamp()}"
    return hashlib.md5(etag.encode()).hexdigest()


def get_permissions_etag(
    request: Request, **_kwargs: dict[str, Any],
) -> str:
    """Return E-Tag for queries dependant on user access permissions."""
    etag = (
        f"{get_instance_timestamp()}"
        f"{get_permission_timestamp()}"
        f"{request.user.id}"
    )
    return hashlib.md5(etag.encode()).hexdigest()


class IsDatasetAllowed(permissions.BasePermission):
    """Checks the permissions to a dataset."""

    def has_permission(self, request: HttpRequest, view: Any) -> bool:
        dataset_id = find_dataset_id_in_request(request)

        if dataset_id is None:
            return True

        return self.has_object_permission(request, view, dataset_id)

    def has_object_permission(
        self, request: HttpRequest, _view: Any, obj: str,
    ) -> bool:
        wgpf_instance = get_wgpf_instance()
        return user_has_permission(
            wgpf_instance.instance_id, cast(User, request.user), obj,
        )

    @staticmethod
    def prepare_allowed_datasets_query() -> str:
        """
        Return query for getting all datasets a user has access to.

        This handles cases in the hierarchy where there are partial rights.
        Query is divided and abstracted into multiple Common Table Expressions.
        The query has a single parameter for user ID and returns rows of
        dataset DB ID and WDAE ID pairs.

        user_to_group joins users with their respective groups.
        dataset_to_group joins datasets with their respective groups.

        from_root and to_root are recursive and walk through the dataset
        hierarchy from a given dataset ID in the respective direction.

        dataset_branch combines from_root and to_root to give all datasets
        present in a dataset hierarchy "branch".
        """
        return textwrap.dedent("""
        WITH RECURSIVE
        --
        user_to_group AS (
            SELECT
                u.id AS uid,
                u.email AS uname,
                g.id AS gid,
                g.name AS gname
            FROM
                users AS u
                LEFT OUTER JOIN users_groups AS ug ON u.id = ug.wdaeuser_id
                LEFT OUTER JOIN auth_group AS g ON ug.group_id = g.id
        ),
        --
        dataset_to_group AS (
            SELECT
                d.id AS did,
                d.dataset_id AS dname,
                g.id AS gid,
                g.name AS gname
            FROM
                datasets_api_dataset AS d
                LEFT OUTER JOIN datasets_api_dataset_groups AS dg
                    ON d.id = dg.dataset_id
                LEFT OUTER JOIN auth_group AS g ON dg.group_id = g.id
        ),
        --
        from_root (
            dataset_id, descendant_id, descendant_wdae_id,
            instance_id, DEPTH
        ) AS (
            SELECT
                t.id AS dataset_id,
                t.id AS descendant_id,
                t.dataset_id AS descendant_wdae_id,
                h.instance_id AS instance_id,
                0
            FROM
                datasets_api_dataset AS t
            LEFT OUTER JOIN datasets_api_datasethierarchy AS h
                ON h.ancestor_id = t.id and h.descendant_id = t.id
            UNION ALL
            SELECT
                t.dataset_id,
                h.descendant_id,
                hd.dataset_id,
                h.instance_id,
                t.DEPTH + 1
            FROM
                from_root AS t
                LEFT OUTER JOIN datasets_api_datasethierarchy AS h
                    ON h.ancestor_id = t.descendant_id
                LEFT OUTER JOIN datasets_api_dataset AS hd
                    ON hd.id = h.descendant_id
            WHERE
                1 = 1
                AND h.ancestor_id <> h.descendant_id
                AND h.direct = TRUE
                AND h.id IS NOT NULL
        ),
        to_root (
            dataset_id, ancestor_id, ancestor_wdae_id,
            instance_id, DEPTH
        ) AS (
            SELECT
                t.id AS dataset_id,
                t.id AS ancestor_id,
                t.dataset_id AS ancestor_wdae_id,
                h.instance_id AS instance_id,
                0
            FROM
                datasets_api_dataset AS t
            LEFT OUTER JOIN datasets_api_datasethierarchy AS h
                ON h.ancestor_id = t.id and h.descendant_id = t.id
            UNION ALL
            SELECT
                t.dataset_id,
                h.ancestor_id,
                hd.dataset_id,
                h.instance_id,
                t.DEPTH - 1
            FROM
                to_root AS t
                LEFT OUTER JOIN datasets_api_datasethierarchy AS h
                    ON 1=1
                    AND h.descendant_id = t.ancestor_id
                LEFT OUTER JOIN datasets_api_dataset AS hd
                    ON hd.id = h.ancestor_id
            WHERE
                1 = 1
                AND h.ancestor_id <> h.descendant_id
                AND h.direct = TRUE
                AND h.id IS NOT NULL
        ),
        dataset_branch(
            dataset_id, branch_dataset_id, branch_dataset_wdae_id,
            instance_id
        ) AS (
            SELECT
                to_root.dataset_id,
                to_root.ancestor_id,
                to_root.ancestor_wdae_id,
                to_root.instance_id
            FROM
                to_root
            UNION ALL
            SELECT
                from_root.dataset_id,
                from_root.descendant_id,
                from_root.descendant_wdae_id,
                from_root.instance_id
            FROM
                from_root
        )
        SELECT DISTINCT db.branch_dataset_id, db.branch_dataset_wdae_id
        FROM user_to_group AS ug
        LEFT OUTER JOIN dataset_to_group AS dg ON ug.gid = dg.gid
            OR dg.gname = 'any_user'
        LEFT OUTER JOIN dataset_branch AS db ON db.dataset_id = dg.did
        WHERE
            1=1
            AND dg.gid IS NOT NULL
            AND db.branch_dataset_id IS NOT NULL
            AND ug.uid = %s
            AND db.instance_id = %s
        ORDER BY db.branch_dataset_id;
        """)

    @staticmethod
    def permitted_datasets(user: User, instance_id: str) -> Iterable[str]:
        """Return list of allowed datasets for a specific user."""
        wgpf_instance = get_wgpf_instance()
        dataset_ids = set(wgpf_instance.get_genotype_data_ids())

        if user.is_anonymous:
            db_datasets = {
                ds.dataset_id: ds
                for ds in Dataset.objects.prefetch_related("groups")
            }
            allowed_datasets: set[str] = set()
            for dataset_id, dataset in db_datasets.items():
                for group in dataset.groups.all():
                    if group.name == "any_user":
                        allowed_datasets.add(dataset_id)
                        break

            return allowed_datasets

        user_groups = get_user_groups(user)
        if (
            settings.DISABLE_PERMISSIONS or
            user.is_superuser or
            user.is_staff or
            "admin" in user_groups
        ):
            return dataset_ids

        query = IsDatasetAllowed.prepare_allowed_datasets_query()

        with connection.cursor() as cursor:
            cursor.execute(query, [user.id, instance_id])  # type: ignore

            allowed_datasets_ids = {row[1] for row in cursor.fetchall()}

        return dataset_ids.intersection(allowed_datasets_ids)


def get_wdae_dataset(
    dataset: str,
) -> Dataset | None:
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


def get_wdae_parents(
    instance_id: str, dataset_id: str, direct: bool = False,
) -> list[Dataset]:
    """
    Return list of parent wdae dataset objects.

    Given a dataset ID or DAE genotype data object or WDAE dataset object,
    returns list of parents as WDAE dataset object.
    """
    dataset = get_wdae_dataset(dataset_id)
    if dataset is None:
        return []
    if direct:
        return DatasetHierarchy.get_parents(instance_id, dataset, True)

    return DatasetHierarchy.get_parents(instance_id, dataset)


def get_wdae_children(instance_id: str, dataset_id: str) -> list[Dataset]:
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
    return DatasetHierarchy.get_children(instance_id, dataset)


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


def _user_has_permission_up(
    instance_id: str, user: User, dataset_id: str,
) -> bool:
    """
    Check user permissions on a dataset's parents.

    Checks if a user has access to any of the dataset parents.
    """
    dataset = get_wdae_dataset(dataset_id)
    if dataset is None:
        return True

    for parent in get_wdae_parents(instance_id, dataset.dataset_id):
        if parent is None:
            logger.error("%s has missing parent!", dataset.dataset_id)
            continue
        if _user_has_permission_strict(user, parent.dataset_id):
            return True
    return False


def _user_has_permission_down(
    instance_id: str, user: User, dataset_id: str,
) -> bool:
    """
    Check user permissions on a dataset's children.

    Checks if a user has access to any of the dataset's children.
    """
    dataset = get_wdae_dataset(dataset_id)
    if dataset is None:
        return True

    for child in get_wdae_children(instance_id, dataset.dataset_id):
        if child is None:
            logger.error("%s has missing parent!", dataset.dataset_id)
            continue
        if _user_has_permission_strict(user, child.dataset_id):
            return True
    return False


def check_permissions(
    instance_id: str, dataset: Dataset, groups: list[str] | set[str],
) -> bool:
    """
    Check whether a set of groups has access to a dataset.

    A group is considered related to a dataset if the dataset itself has it,
    if a child of the dataset has it, or if a parent of the dataset has it.
    """
    if len(groups) == 0:
        return False

    groups = list(groups)

    groups_in = ", ".join(["%s" for _ in groups])

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(gr.name) "
            "FROM datasets_api_datasethierarchy as hr "
            "JOIN datasets_api_dataset_groups as dsgr "
            "ON hr.ancestor_id = dsgr.dataset_id "
            "OR hr.descendant_id = dsgr.dataset_id "
            "JOIN auth_group as gr on gr.id = dsgr.group_id "
            "WHERE (ancestor_id = %s OR descendant_id = %s) "
            "AND instance_id = %s"
            f"AND gr.name IN ({groups_in}) "
            "GROUP BY ancestor_id, descendant_id;",
            [dataset.id, dataset.id, instance_id, *groups],
        )
        rows = list(cursor.fetchall())

    return len(rows) > 0


def check_permissions_up(
    instance_id: str, dataset: Dataset, groups: list[str] | set[str],
) -> bool:
    """
    Check whether a set of groups has access to a dataset only through parents.

    This includes the dataset's own groups and any groups to parents.
    """
    if len(groups) == 0:
        return False

    groups = list(groups)

    groups_in = ", ".join(["%s" for _ in groups])

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(gr.name) "
            "FROM datasets_api_datasethierarchy as hr "
            "JOIN datasets_api_dataset_groups as dsgr "
            "ON hr.ancestor_id = dsgr.dataset_id "
            "OR hr.descendant_id = dsgr.dataset_id "
            "JOIN auth_group as gr on gr.id = dsgr.group_id "
            "WHERE descendant_id = %s "
            "AND instance_id = %s"
            f"AND gr.name IN ({groups_in}) "
            "GROUP BY ancestor_id, descendant_id;",
            [dataset.id, instance_id, *groups],
        )
        rows = list(cursor.fetchall())

    return len(rows) > 0


def user_has_permission(instance_id: str, user: User, dataset_id: str) -> bool:
    """Check if a user has permission to browse the given dataset."""
    if settings.DISABLE_PERMISSIONS:
        return True
    if user.is_superuser or user.is_staff:
        return True
    user_groups = get_user_groups(user)
    if "admin" in user_groups:
        return True

    logger.debug("checking user <%s> permissions on %s", user, dataset_id)
    dataset = get_wdae_dataset(dataset_id)
    if dataset is None:
        return True

    return check_permissions(instance_id, dataset, user_groups)


def get_allowed_genotype_studies(
    instance_id: str, user: User, dataset_id: str,
) -> set[str]:
    """Collect and return genotype study IDs the user has access to."""
    skip_check = False
    if settings.DISABLE_PERMISSIONS or user.is_superuser or user.is_staff:
        skip_check = True
    user_groups = get_user_groups(user)
    if "admin" in user_groups:
        skip_check = True
    allowed_studies = set()
    dataset = get_wdae_dataset(dataset_id)
    if dataset is None:
        return set()

    if DatasetHierarchy.is_study(instance_id, dataset):
        if skip_check or check_permissions_up(
            instance_id, dataset, user_groups,
        ):
            allowed_studies.add(dataset.dataset_id)
        return allowed_studies

    for child in get_wdae_children(instance_id, dataset.dataset_id):
        if DatasetHierarchy.is_study(instance_id, child):
            if skip_check or check_permissions_up(
                instance_id, child, user_groups,
            ):
                allowed_studies.add(child.dataset_id)

    return set(allowed_studies)


def get_allowed_genotype_data(
    instance_id: str, user: User, dataset_id: str,
) -> set[str]:
    """Collect and return genotype data IDs the user has access to."""
    allowed_genotype_data = []
    dataset = get_wdae_dataset(dataset_id)
    if dataset is None:
        return set()
    for child in get_wdae_children(instance_id, dataset.dataset_id):
        if (
            _user_has_permission_strict(user, child.dataset_id)
            or _user_has_permission_up(instance_id, user, child.dataset_id)
        ):
            allowed_genotype_data.append(child.dataset_id)
    if len(allowed_genotype_data) > 0:
        allowed_genotype_data.append(dataset.dataset_id)
    return set(allowed_genotype_data)


def get_dataset_info(dataset_id: str) -> dict[str, Any] | None:
    """Return a dictionary describing a Dataset object."""
    dataset = get_wdae_dataset(dataset_id)
    if dataset is None:
        logger.error("Could not find WDAE dataset for %s", dataset_id)
        return None
    return {
        "datasetName": dataset.dataset_name,
        "datasetId": dataset.dataset_id,
        "broken": dataset.broken,
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
                "Dataset %s found in DAE, but not in WDAE!", dataset_id,
            )
            result.append({
                "datasetName": dataset_id,
                "datasetId": dataset_id,
                "broken": True,
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
        else ds["datasetId"],

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
    if user.is_anonymous:
        return {"any_user"}
    return {g.name for g in user.groups.all()}


def get_dataset_groups(dataset: str | Dataset) -> set[str]:
    # pylint: disable=no-member
    if not isinstance(dataset, Dataset):
        dataset = Dataset.objects.get(dataset_id=force_str(dataset))
    return {g.name for g in dataset.groups.all()}


def handle_partial_permissions(
        instance_id: str, user: User, dataset_id: str, request_data: dict,
) -> None:
    """Handle partial permission on a dataset.

    A user may have only partial access to a dataset based
    on which of its constituent studies he has rights to access.
    This method attaches these rights to the request as study filters
    in order to filter variants from studies the user cannot access.
    """
    request_data["allowed_studies"] = \
        get_allowed_genotype_studies(instance_id, user, dataset_id)
