import logging
import os
from typing import Any, Optional, Union, cast

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from groups_api.serializers import GroupSerializer
from query_base.query_base import QueryBaseView
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from studies.study_wrapper import StudyWrapper, StudyWrapperBase

from datasets_api.permissions import get_instance_timestamp_etag, get_permissions_etag, \
    get_wdae_parents, user_has_permission
from dae.studies.study import GenotypeData

from .models import Dataset, DatasetHierarchy

from django.views.decorators.http import etag
from django.utils.decorators import method_decorator


logger = logging.getLogger(__name__)


def augment_accessibility(
    instance_id: str, dataset: dict[str, Any], user: User,
) -> dict[str, Any]:
    """Augment a dataset response JSON with access_rights section."""
    # pylint: disable=no-member
    dataset["access_rights"] = user_has_permission(
        instance_id, user, dataset["id"],
    )
    return dataset


def augment_with_groups(
    dataset: dict[str, Any], db_dataset: Optional[Dataset] = None,
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

def produce_description_hierarchy(
    dataset: GenotypeData,
    selected: list[str],
    indent_level: int = 0
) -> str:
    """Create dataset description hierarchy from dataset children."""
    if dataset.is_group:
        res = []
        indent = "\t" * indent_level
        for child in dataset.studies:
            if child.study_id in selected:
                child_descriptions = produce_description_hierarchy(
                    child,
                    selected,
                    indent_level + 1
                )
                res.append(
                    f"{indent}- **[{child.name}](datasets/{child.study_id})** "
                    f"{get_first_paragraph(child.description)}\n"
                    f"{child_descriptions}"
                )
        return "\n".join(res)

    return ""


def get_first_paragraph(
    text: Union[str, None],
) -> str:
    """Get first paragraph of text."""
    result = ""
    if text is not None:
        paragraphs = text.split("\n\n")
        if paragraphs[0].startswith("#"):
            title_match = re.match("^##((?:\n|.)*?)$\n", paragraphs[0])
            result = re.sub("^##((?:\n|.)*?)$\n", "", paragraphs[0]) \
                if title_match else paragraphs[1]
        else:
            result = paragraphs[0]

    return result.replace("\n", " ").strip()


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

        res = [augment_accessibility(self.instance_id, ds, user) for ds in res]
        res = [augment_with_groups(ds, db_datasets[ds["id"]]) for ds in res]

        for result in res:
            result["parents"] = []
            if result["id"] in parents:
                result["parents"] = [parents[result["id"]].dataset_id]

        return res


    @method_decorator(etag(get_permissions_etag))
    def get(
        self, request: Request, dataset_id: Optional[str] = None,
    ) -> Response:
        """Return response to a get request for a dataset or all datasets."""
        user = request.user

        if dataset_id is None:
            return Response({"data": self._collect_datasets_summary(user)})

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)

        if not dataset:
            return Response({"error": f"Dataset {dataset_id} not found"},
                            status=status.HTTP_404_NOT_FOUND)

        dataset_object = Dataset.objects.get(dataset_id=dataset_id)

        if user_has_permission(
            self.instance_id, user, dataset_object.dataset_id,
        ):
            person_set_collection_configs = {
                psc.id: psc.domain_json()
                for psc in dataset.person_set_collections.values()
            }
            res = StudyWrapperBase.build_genotype_data_description(
                self.gpf_instance,
                dataset.config,
                dataset.description,
                person_set_collection_configs,
            )
        else:
            res = StudyWrapperBase.build_genotype_data_all_datasets(
                dataset.config,
            )
            res["description"] = dataset.description

        res = augment_accessibility(self.instance_id, res, user)
        res = augment_with_groups(res)
        res = augment_with_parents(self.instance_id, res)

        raw_study = dataset.genotype_data_study \
            if isinstance(dataset, StudyWrapper) \
            else dataset.remote_genotype_data
        if dataset.is_group:
            visible_datasets = self.gpf_instance.get_visible_datasets()
            visible_datasets = visible_datasets if visible_datasets else []
            genotype_data_ids = [
                gd_id for gd_id in dataset.get_studies_ids()
                if gd_id in visible_datasets and gd_id != dataset.study_id
            ]
            if genotype_data_ids:
                descriptions = produce_description_hierarchy(
                    raw_study, genotype_data_ids,
                )
                res["children_description"] = (
                    "\nThis dataset includes:\n"
                    f"{descriptions}"
                )
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

        res = [augment_accessibility(self.instance_id, ds, user) for ds in res]
        res = [augment_with_groups(ds) for ds in res]
        res = [augment_with_parents(self.instance_id, ds) for ds in res]
        return res

    def get(self, request: Request) -> Response:
        user = request.user

        return Response({"data": self._collect_datasets_summary(user)})


class PermissionDeniedPromptView(QueryBaseView):
    """Provide the markdown-formatted permission denied prompt text."""

    def __init__(self) -> None:
        super().__init__()

        dae_config = self.gpf_instance.dae_config
        default_prompt = (
            "The Genotype and Phenotype in Families (GPF) data is"
            " accessible by registered users. Contact the system"
            " administrator of the GPF system to get an account in"
            " the system and get permission to access the data."
        )
        if dae_config.gpfjs is None or \
                dae_config.gpfjs.permission_denied_prompt_file is None:
            self.permission_denied_prompt = default_prompt
        else:
            prompt_filepath = dae_config.gpfjs.permission_denied_prompt_file

            if not os.path.exists(prompt_filepath) or\
                    not os.path.isfile(prompt_filepath):
                self.permission_denied_prompt = default_prompt
            else:
                with open(prompt_filepath, "r") as infile:
                    self.permission_denied_prompt = infile.read()

    @method_decorator(etag(get_instance_timestamp_etag))
    def get(self, _request: Request) -> Response:
        return Response({"data": self.permission_denied_prompt})


class DatasetDetailsView(QueryBaseView):
    """Provide miscellaneous details for a given dataset."""

    def get(self, request: Request, dataset_id: str) -> Response:
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

    def get(self, request: Request, dataset_id: str, column: str) -> Response:
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

    def get(
        self, request: Request, dataset_id: Optional[str] = None,
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

    def get(
        self, request: Request, dataset_id: str,
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

        return Response(status=status.HTTP_200_OK)


class BaseDatasetPermissionsView(QueryBaseView):
    """Base dataset permission view."""

    def _get_dataset_info(self, dataset: Dataset) -> Optional[dict[str, Any]]:
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
        users_list = sorted(users_list, key=lambda d: d["email"])

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

    def get(self, request: Request) -> Response:
        """Return dataset permissions details."""
        dataset_search = request.GET.get("search")
        page = request.GET.get("page", 1)
        query = Dataset.objects
        if dataset_search is not None and dataset_search != "":
            query = query.filter(  # type: ignore
                dataset_id__icontains=dataset_search)

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

    def get(self, request: Request, dataset_id: str) -> Response:
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
    """Provide the hierarchy of all datasets configured in the instance."""

    @staticmethod
    def produce_tree(
        instance_id: str, dataset: GenotypeData,
        user: User, selected: list[str],
    ) -> Optional[dict[str, Any]]:
        """Recursively collect a dataset's id, children and access rights."""
        has_rights = user_has_permission(instance_id, user, dataset.study_id)
        dataset_obj = Dataset.objects.get(dataset_id=dataset.study_id)
        groups = dataset_obj.groups.all()
        if "hidden" in [group.name for group in groups] and not has_rights:
            return None

        children = None
        if dataset.is_group:
            children = []
            for child in dataset.studies:
                if child.study_id in selected:
                    tree = DatasetHierarchyView.produce_tree(
                        instance_id, child, user, selected,
                    )
                    if tree is not None:
                        children.append(tree)

        return {
            "dataset": dataset.study_id,
            "name": dataset.name,
            "children": children,
            "access_rights": has_rights,
        }

    def get(self, request: Request) -> Response:
        """Return the hierarchy of configured datasets in the instance."""
        user = request.user
        genotype_data_ids = self.gpf_instance.get_genotype_data_ids()
        genotype_data = filter(lambda gd: gd and not gd.parents, [
            self.gpf_instance.get_wdae_wrapper(genotype_data_id)
            for genotype_data_id in genotype_data_ids
        ])

        trees = []

        for gd in genotype_data:
            tree = DatasetHierarchyView.produce_tree(
                self.instance_id, gd, user, genotype_data_ids,
            )
            if tree is not None:
                trees.append(tree)

        return Response({"data": trees}, status=status.HTTP_200_OK)


class VisibleDatasetsView(QueryBaseView):
    """Provide a list of which datasets to show in the frontend."""

    def get(self, request: Request) -> Response:
        """Return the list of visible datasets."""
        # pylint: disable=unused-argument
        res = self.gpf_instance.get_visible_datasets()
        if not res:
            res = sorted(self.gpf_instance.get_genotype_data_ids())
        return Response(res)
