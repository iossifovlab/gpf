import logging
from collections.abc import Iterable
from operator import itemgetter
from typing import Any, cast

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.http import etag
from gpf_instance.gpf_instance import (
    calc_and_set_cacheable_hash,
    get_cacheable_hash,
)
from groups_api.serializers import GroupSerializer
from query_base.query_base import QueryBaseView
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from studies.study_wrapper import StudyWrapperBase

from dae.studies.study import GenotypeData
from datasets_api.permissions import (
    IsDatasetAllowed,
    get_instance_timestamp_etag,
    get_permissions_etag,
    get_wdae_parents,
    user_has_permission,
)

from .models import Dataset, DatasetHierarchy

logger = logging.getLogger(__name__)


def augment_accessibility(
    dataset: dict[str, Any], allowed_datasets: Iterable[str],
) -> dict[str, Any]:
    """Augment a dataset response JSON with access_rights section."""
    # pylint: disable=no-member
    dataset["access_rights"] = dataset["id"] in allowed_datasets

    return dataset


def augment_with_groups(
    dataset: dict[str, Any], db_dataset: Dataset | None = None,
) -> dict[str, Any]:
    """Add groups to response object."""
    # pylint: disable=no-member
    if db_dataset is None:
        db_dataset = Dataset.objects.get(dataset_id=dataset["id"])
    serializer = GroupSerializer(db_dataset.groups.all(), many=True)
    dataset["groups"] = serializer.data
    return dataset


def augment_with_parents(
    instance_id: str, dataset: dict[str, Any],
) -> dict[str, Any]:
    """Augment a dataset response JSON with parents section."""
    dataset["parents"] = [
        ds.dataset_id for ds in get_wdae_parents(
            instance_id, dataset["id"], direct=True,
        )
    ]
    return dataset


def get_description_etag(
    request: Request, **_kwargs: dict[str, Any],
) -> str | None:
    """Get description etag."""
    dataset_id = request.parser_context["kwargs"]["dataset_id"]

    return get_cacheable_hash(f"{dataset_id}_description")


class DatasetView(QueryBaseView):
    """
    General dataset view.

    Provides either a summary of ALL available dataset configs
    or a specific dataset configuration in full, depending on
    whether the request is made with a dataset_id param or not.
    """

    def _collect_datasets_summary(
        self, user: User,
    ) -> list[dict[str, Any]]:
        genotype_data = self.gpf_instance.get_genotype_data_ids()

        datasets: list[StudyWrapperBase] = cast(
            list[StudyWrapperBase],
            filter(None, [
                self.gpf_instance.get_wdae_wrapper(genotype_data_id)
                for genotype_data_id in genotype_data
            ]),
        )

        res = [
            StudyWrapperBase.build_genotype_data_all_datasets(dataset.config)
            for dataset in datasets
        ]

        db_datasets = {
            ds.dataset_id: ds
            for ds in Dataset.objects.prefetch_related("groups")
        }

        parents = DatasetHierarchy.get_direct_datasets_parents(
            self.instance_id,
            db_datasets.values(),
        )

        allowed_datasets = self.get_permitted_datasets(user)

        res = [augment_accessibility(ds, allowed_datasets) for ds in res]
        res = [augment_with_groups(ds, db_datasets[ds["id"]]) for ds in res]

        for result in res:
            if result["id"] in parents:
                result["parents"] = parents[result["id"]]

        return res

    @method_decorator(etag(get_permissions_etag))
    def get(
        self, request: Request, dataset_id: str | None = None,
    ) -> Response:
        """Return response to a get request for a dataset or all datasets."""
        user = request.user

        if dataset_id is None:
            return Response({"data": self._collect_datasets_summary(user)})

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)

        if not dataset:
            return Response({"error": f"Dataset {dataset_id} not found"},
                            status=status.HTTP_404_NOT_FOUND)

        person_set_collection_configs = {
            psc.id: psc.domain_json()
            for psc in dataset.person_set_collections.values()
        }
        res = StudyWrapperBase.build_genotype_data_description(
            self.gpf_instance,
            dataset.config,
            person_set_collection_configs,
        )

        allowed_datasets = self.get_permitted_datasets(user)

        res = augment_accessibility(res, allowed_datasets)
        res = augment_with_groups(res)
        res = augment_with_parents(self.instance_id, res)

        return Response({"data": res})


class StudiesView(QueryBaseView):
    """View class for genotype data stuides and datasets."""

    def _collect_datasets_summary(
        self, user: User,
    ) -> list[dict[str, Any]]:
        genotype_data_ids = self.gpf_instance.get_genotype_data_ids()

        datasets: list[StudyWrapperBase] = []
        for genotype_data_id in genotype_data_ids:
            study = self.gpf_instance.get_wdae_wrapper(genotype_data_id)
            if study is None or study.is_group:
                continue
            datasets.append(study)

        res = []
        for dataset in datasets:
            assert dataset is not None

            res.append(
                StudyWrapperBase.build_genotype_data_all_datasets(
                    dataset.config))

        allowed_datasets = self.get_permitted_datasets(user)

        res = [augment_accessibility(ds, allowed_datasets) for ds in res]
        res = [augment_with_groups(ds) for ds in res]
        return [augment_with_parents(self.instance_id, ds) for ds in res]

    @method_decorator(etag(get_permissions_etag))
    def get(self, request: Request) -> Response:
        user = request.user

        return Response({"data": self._collect_datasets_summary(user)})


class DatasetDetailsView(QueryBaseView):
    """Provide miscellaneous details for a given dataset."""

    @method_decorator(etag(get_instance_timestamp_etag))
    def get(self, _request: Request, dataset_id: str) -> Response:
        # pylint: disable=unused-argument
        """Return response for a specific dataset configuration details."""
        genotype_data_config = \
            self.gpf_instance.get_genotype_data_config(dataset_id)
        if genotype_data_config is None:
            return Response(
                {"error": f"Dataset {dataset_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        has_denovo = genotype_data_config.get("has_denovo", False)

        dataset_details = {
            "hasDenovo": has_denovo,
            "genome": genotype_data_config.genome,
            "chrPrefix": genotype_data_config.chr_prefix,
        }
        return Response(dataset_details)


class DatasetPedigreeView(QueryBaseView):
    """Provide pedigree data for a given dataset."""

    @method_decorator(etag(get_instance_timestamp_etag))
    def get(self, _request: Request, dataset_id: str, column: str) -> Response:
        # pylint: disable=unused-argument
        """Return response for a pedigree get request for pedigree column."""
        genotype_data = self.gpf_instance.get_genotype_data(dataset_id)

        if genotype_data is None:
            return Response(
                {"error": f"Dataset {dataset_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if column not in genotype_data.families.ped_df.columns:
            return Response(
                {"error": f"No such column {column}"},
                status=status.HTTP_404_NOT_FOUND,
            )

        values_domain = list(
            map(str, genotype_data.families.ped_df[column].unique()),
        )

        return Response(
            {"column_name": column, "values_domain": values_domain},
        )


class DatasetConfigView(DatasetView):
    """Provide a dataset's configuration. Used for remote instances."""

    @method_decorator(etag(get_instance_timestamp_etag))
    def get(
        self, _request: Request, dataset_id: str | None = None,
    ) -> Response:
        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        genotype_data = self.gpf_instance.get_genotype_data(dataset_id)

        if genotype_data is None:
            return Response(
                {"error": f"Dataset {dataset_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(augment_with_parents(
            self.instance_id, genotype_data.config.to_dict(),
        ))


class DatasetDescriptionView(QueryBaseView):
    """Provide fetching and editing a dataset's description."""

    @method_decorator(etag(get_description_etag))
    def get(
        self, _request: Request, dataset_id: str | None,
    ) -> Response:
        # pylint: disable=unused-argument
        """Collect a dataset's description."""
        if dataset_id is None:
            return Response(
                {"error": "No dataset id provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        genotype_data = self.gpf_instance.get_genotype_data(dataset_id)
        if genotype_data is None:
            return Response(
                {"error": f"Dataset {dataset_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if get_cacheable_hash(dataset_id) is None:
            calc_and_set_cacheable_hash(f"{dataset_id}_description",
                               genotype_data.description)

        return Response(
            {"description": genotype_data.description},
            status=status.HTTP_200_OK,
        )

    def post(self, request: Request, dataset_id: str) -> Response:
        """Overwrite a dataset's description."""
        if not request.user.is_staff:
            return Response(
                {"error": "You have no permission to edit the description."},
                status=status.HTTP_403_FORBIDDEN,
            )

        description = request.data.get("description")
        genotype_data = self.gpf_instance.get_genotype_data(dataset_id)
        genotype_data.description = description
        calc_and_set_cacheable_hash(f"{dataset_id}_description",
                           genotype_data.description)

        return Response(status=status.HTTP_200_OK)


class BaseDatasetPermissionsView(QueryBaseView):
    """Base dataset permission view."""

    def _get_dataset_info(self, dataset: Dataset) -> dict[str, Any] | None:
        groups = dataset.groups.all()
        group_names = sorted([group.name for group in groups])

        user_model = get_user_model()
        users_list = []
        users_found = set()
        for group in groups:
            users = user_model.objects.filter(
                groups__name=group.name,
            ).all()
            for user in users:
                if user.email not in users_found:
                    users_list += [
                        {"name": user.name, "email": user.email},
                    ]
                    users_found.add(user.email)
        users_list = sorted(users_list, key=itemgetter("email"))

        dataset_gd = self.gpf_instance.get_genotype_data(
            dataset.dataset_id,
        )

        if dataset_gd is None:
            logger.error(
                "Dataset %s missing in GPF instance!",
                dataset.dataset_id,
            )
            return None

        name = dataset_gd.name
        if name is None:
            name = ""

        return {
            "dataset_id": dataset_gd.study_id,
            "dataset_name": name,
            "broken": dataset.broken,
            "users": users_list,
            "groups": group_names,

        }


class DatasetPermissionsView(BaseDatasetPermissionsView):
    """Dataset permissions view."""

    page_size = settings.REST_FRAMEWORK["PAGE_SIZE"]

    @method_decorator(etag(get_permissions_etag))
    def get(self, request: Request) -> Response:
        """Return dataset permissions details."""

        if not request.user.is_staff:
            return Response(
                {"error": "You have no permission to edit the description."},
                status=status.HTTP_403_FORBIDDEN,
            )

        dataset_search = request.GET.get("search")
        page = request.GET.get("page", 1)
        query = Dataset.objects
        if dataset_search is not None and dataset_search != "":
            query = query.filter(  # type: ignore
                dataset_name__icontains=dataset_search)

        if page is None:
            return Response(status.HTTP_400_BAD_REQUEST)
        if isinstance(page, str):
            page = int(page)

        page_start = (page - 1) * self.page_size
        page_end = page * self.page_size
        datasets = query.all().order_by("dataset_id")[page_start:page_end]

        dataset_details = []
        for dataset in datasets:
            info = self._get_dataset_info(dataset)

            if info is None:
                continue

            dataset_details.append(info)

        if len(dataset_details) == 0:
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(dataset_details)


class DatasetPermissionsSingleView(BaseDatasetPermissionsView):
    """Single dataset permission view."""

    page_size = settings.REST_FRAMEWORK["PAGE_SIZE"]

    def get(self, _request: Request, dataset_id: str) -> Response:
        # pylint: disable=unused-argument
        """Return dataset permission details."""
        try:
            dataset = Dataset.objects.get(dataset_id=dataset_id)
        except Dataset.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        dataset_details = self._get_dataset_info(dataset)

        if dataset_details is None:
            return Response({}, status=status.HTTP_404_NOT_FOUND)

        return Response(dataset_details)


class DatasetHierarchyView(QueryBaseView):
    """Provide the hierarchy of one dataset configured in the instance."""

    def produce_tree(
        self,
        dataset: GenotypeData,
        selected: list[str],
        permitted_datasets: set[str],
    ) -> dict[str, Any] | None:
        """Recursively collect a dataset's id, children and access rights."""
        has_rights = dataset.study_id in permitted_datasets
        dataset_obj = Dataset.objects.get(dataset_id=dataset.study_id)
        groups = dataset_obj.groups.all()
        if "hidden" in [group.name for group in groups] and not has_rights:
            return None

        children = None
        if dataset.is_group:
            children = []
            for child in dataset.studies:
                if child.study_id in selected:
                    tree = self.produce_tree(
                        child, selected, permitted_datasets,
                    )
                    if tree is not None:
                        children.append(tree)

        return {
            "dataset": dataset.study_id,
            "name": dataset.name,
            "children": children,
            "access_rights": has_rights,
        }

    @method_decorator(etag(get_permissions_etag))
    def get(self, request: Request, dataset_id: str | None = None) -> Response:
        """Return the hierarchy of one dataset in the instance."""
        user = request.user

        genotype_data_ids = self.gpf_instance.get_genotype_data_ids()

        permitted_datasets = set(
            IsDatasetAllowed.permitted_datasets(user, self.instance_id),
        )

        if dataset_id:
            genotype_data = self.gpf_instance.get_genotype_data(dataset_id)

            tree = self.produce_tree(
                genotype_data, genotype_data_ids, permitted_datasets,
            )

            return Response({"data": tree}, status=status.HTTP_200_OK)

        genotype_datas = filter(lambda gd: gd and not gd.parents, [
            self.gpf_instance.get_wdae_wrapper(genotype_data_id)
            for genotype_data_id in genotype_data_ids
        ])

        trees = []

        for gd in genotype_datas:
            tree = self.produce_tree(
                gd,
                genotype_data_ids,
                permitted_datasets,
            )
            if tree is not None:
                trees.append(tree)

        return Response({"data": trees}, status=status.HTTP_200_OK)


class VisibleDatasetsView(QueryBaseView):
    """Provide a list of which datasets to show in the frontend."""

    @method_decorator(etag(get_instance_timestamp_etag))
    def get(self, _request: Request) -> Response:
        """Return the list of visible datasets."""
        # pylint: disable=unused-argument
        res = self.gpf_instance.get_visible_datasets()
        if not res:
            res = sorted(self.gpf_instance.get_genotype_data_ids())
        return Response(res)
