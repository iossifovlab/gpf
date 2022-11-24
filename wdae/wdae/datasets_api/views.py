import os
import logging

from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework.response import Response  # type: ignore
from rest_framework import status  # type: ignore

from query_base.query_base import QueryBaseView
from studies.study_wrapper import StudyWrapperBase

from groups_api.serializers import GroupSerializer
from datasets_api.permissions import get_wdae_parents, user_has_permission
from dae.studies.study import GenotypeData
from .models import Dataset


logger = logging.getLogger(__name__)


def augment_accessibility(dataset, user):
    # pylint: disable=no-member
    dataset_object = Dataset.objects.get(dataset_id=dataset["id"])
    dataset["access_rights"] = user_has_permission(user, dataset_object)
    return dataset


def augment_with_groups(dataset):
    # pylint: disable=no-member
    dataset_object = Dataset.objects.get(dataset_id=dataset["id"])
    serializer = GroupSerializer(dataset_object.groups.all(), many=True)
    dataset["groups"] = serializer.data
    return dataset


def augment_with_parents(dataset):
    dataset["parents"] = [
        ds.dataset_id for ds in get_wdae_parents(dataset["id"])
    ]
    return dataset


class DatasetView(QueryBaseView):
    """
    General dataset view.

    Provides either a summary of ALL available dataset configs
    or a specific dataset configuration in full, depending on
    whether the request is made with a dataset_id param or not.
    """

    def _collect_datasets_summary(self, user):
        selected_genotype_data = \
            self.gpf_instance.get_selected_genotype_data() \
            or self.gpf_instance.get_genotype_data_ids()

        datasets = filter(None, [
            self.gpf_instance.get_wdae_wrapper(genotype_data_id)
            for genotype_data_id in selected_genotype_data
        ])

        res = [
            StudyWrapperBase.build_genotype_data_all_datasets(
                dataset.config
            )
            for dataset in datasets
        ]

        if not self.gpf_instance.get_selected_genotype_data():
            res = sorted(res, key=lambda desc: desc["name"])

        res = [augment_accessibility(ds, user) for ds in res]
        res = [augment_with_groups(ds) for ds in res]
        res = [augment_with_parents(ds) for ds in res]
        return res

    def get(self, request, dataset_id=None):
        user = request.user

        if dataset_id is None:
            return Response({"data": self._collect_datasets_summary(user)})

        dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)

        if not dataset:
            return Response({"error": f"Dataset {dataset_id} not found"},
                            status=status.HTTP_404_NOT_FOUND)

        if dataset:
            # pylint: disable=no-member
            dataset_object = Dataset.objects.get(dataset_id=dataset_id)

            if user_has_permission(user, dataset_object):
                person_set_collection_configs = {
                    psc.id: psc.config_json()
                    for psc in dataset.person_set_collections.values()
                }
                res = StudyWrapperBase.build_genotype_data_group_description(
                    self.gpf_instance,
                    dataset.config,
                    dataset.description,
                    person_set_collection_configs
                )
            else:
                res = StudyWrapperBase.build_genotype_data_all_datasets(
                    dataset.config
                )

            res = augment_accessibility(res, user)
            res = augment_with_groups(res)
            res = augment_with_parents(res)

            return Response({"data": res})


class StudiesView(QueryBaseView):
    def _collect_datasets_summary(self, user):
        selected_genotype_data = \
            self.gpf_instance.get_selected_genotype_data() \
            or self.gpf_instance.get_genotype_data_ids()

        datasets = filter(lambda study: study.is_group is False, [
            self.gpf_instance.get_wdae_wrapper(genotype_data_id)
            for genotype_data_id in selected_genotype_data
        ])

        res = [
            StudyWrapperBase.build_genotype_data_all_datasets(
                dataset.config
            )
            for dataset in datasets
        ]

        if not self.gpf_instance.get_selected_genotype_data():
            res = sorted(res, key=lambda desc: desc["name"])

        res = [augment_accessibility(ds, user) for ds in res]
        res = [augment_with_groups(ds) for ds in res]
        res = [augment_with_parents(ds) for ds in res]
        return res

    def get(self, request):
        user = request.user

        return Response({"data": self._collect_datasets_summary(user)})


class PermissionDeniedPromptView(QueryBaseView):
    """Provide the markdown-formatted permission denied prompt text."""

    def __init__(self):
        super(PermissionDeniedPromptView, self).__init__()

        dae_config = self.gpf_instance.dae_config
        if dae_config.gpfjs is None or \
                dae_config.gpfjs.permission_denied_prompt_file is None:
            self.permission_denied_prompt = ""
        else:
            prompt_filepath = dae_config.gpfjs.permission_denied_prompt_file

            if not os.path.exists(prompt_filepath) or\
                    not os.path.isfile(prompt_filepath):
                self.permission_denied_prompt = ""
            else:
                with open(prompt_filepath, "r") as infile:
                    self.permission_denied_prompt = infile.read()

    def get(self, request):
        return Response({"data": self.permission_denied_prompt})


class DatasetDetailsView(QueryBaseView):
    """Provide miscellaneous details for a given dataset."""

    def get(self, request, dataset_id):
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

    def get(self, request, dataset_id, column):
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
            map(str, genotype_data.families.ped_df[column].unique())
        )

        return Response(
            {"column_name": column, "values_domain": values_domain}
        )


class DatasetConfigView(DatasetView):
    """Provide a dataset's configuration. Used for remote instances."""

    def get(self, request, dataset_id=None):
        genotype_data = self.gpf_instance.get_genotype_data(dataset_id)

        if genotype_data is None:
            return Response(
                {"error": f"Dataset {dataset_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(augment_with_parents(genotype_data.config.to_dict()))


class DatasetDescriptionView(QueryBaseView):
    """Provide fetching and editing a dataset's description."""

    def get(self, request, dataset_id):  # pylint: disable=unused-argument
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
            status=status.HTTP_200_OK
        )

    def post(self, request, dataset_id):
        """Overwrite a dataset's description."""
        if not request.user.is_staff:
            return Response(
                {"error": "You have no permission to edit the description."},
                status=status.HTTP_403_FORBIDDEN
            )

        description = request.data.get("description")
        genotype_data = self.gpf_instance.get_genotype_data(dataset_id)
        genotype_data.description = description

        return Response(status=status.HTTP_200_OK)


class DatasetPermissionsView(QueryBaseView):

    page_size = settings.REST_FRAMEWORK["PAGE_SIZE"]

    def get(self, request):
        dataset_search = request.GET.get("search")
        page = request.GET.get("page", 1)
        query = Dataset.objects
        if dataset_search is not None and dataset_search != "":
            query = query.filter(dataset_id__icontains=dataset_search)

        if page is None:
            return Response(status.HTTP_400_BAD_REQUEST)
        if isinstance(page, str):
            page = int(page)

        page_start = (page - 1) * self.page_size
        page_end = page * self.page_size
        datasets = query.all()[page_start:page_end]

        dataset_details = []
        for dataset in datasets:
            groups = dataset.groups.all()
            group_names = [group.name for group in groups]

            user_model = get_user_model()
            users_list = []
            for group in groups:
                users = user_model.objects.filter(
                    groups__name=group.name
                ).all()
                users_list += [
                    {"name": user.name, "email": user.email}
                    for user in users
                ]

            dataset_gd = self.gpf_instance.get_genotype_data(
                dataset.dataset_id
            )

            if dataset_gd is None:
                logger.warning(
                    "Dataset %s missing in GPF instance!",
                    dataset.dataset_id
                )
                dataset_details.append({
                    "dataset_id": dataset.dataset_id,
                    "dataset_name": "Missing dataset",
                    "users": [],
                    "groups": []
                })
                continue

            name = dataset_gd.name
            if name is None:
                name = ""

            dataset_details.append({
                "dataset_id": dataset_gd.study_id,
                "dataset_name": name,
                "broken": dataset.broken,
                "users": users_list,
                "groups": group_names

            })

        if len(dataset_details) == 0:
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(dataset_details)


class DatasetHierarchyView(QueryBaseView):
    """Provide the hierarchy of all datasets configured in the instance."""

    @staticmethod
    def produce_tree(dataset: GenotypeData, user, selected):
        """Recursively collect a dataset's id, children and access rights."""
        children = None
        if dataset.is_group:
            children = [
                DatasetHierarchyView.produce_tree(child, user, selected)
                for child in dataset.studies
                if child.study_id in selected
            ]
        # pylint: disable=no-member
        dataset_object = Dataset.objects.get(dataset_id=dataset.study_id)
        return {
            "dataset": dataset.study_id,
            "name": dataset.name,
            "children": children,
            "access_rights": user_has_permission(user, dataset_object)
        }

    def get(self, request):
        """Return the hierarchy of configured datasets in the instance."""
        user = request.user
        selected_genotype_data = \
            self.gpf_instance.get_selected_genotype_data() \
            or self.gpf_instance.get_genotype_data_ids()
        genotype_data = filter(lambda gd: gd and not gd.parents, [
            self.gpf_instance.get_wdae_wrapper(genotype_data_id)
            for genotype_data_id in selected_genotype_data
        ])
        return Response({"data": [
            DatasetHierarchyView.produce_tree(gd, user, selected_genotype_data)
            for gd in genotype_data
        ]}, status=status.HTTP_200_OK)
