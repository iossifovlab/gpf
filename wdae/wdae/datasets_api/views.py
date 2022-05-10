import os

from rest_framework.response import Response  # type: ignore
from rest_framework import status  # type: ignore
from guardian.shortcuts import get_groups_with_perms  # type: ignore

from query_base.query_base import QueryBaseView
from studies.study_wrapper import StudyWrapperBase

from .models import Dataset
from groups_api.serializers import GroupSerializer
from datasets_api.permissions import get_wdae_parents, \
    user_has_permission


class DatasetView(QueryBaseView):

    def augment_accessibility(self, dataset, user):
        dataset_object = Dataset.objects.get(dataset_id=dataset["id"])

        dataset["access_rights"] = user_has_permission(
            user, dataset_object)

        return dataset

    def augment_with_groups(self, dataset):
        dataset_object = Dataset.objects.get(dataset_id=dataset["id"])
        groups = get_groups_with_perms(dataset_object)
        serializer = GroupSerializer(groups, many=True)
        dataset["groups"] = serializer.data

        return dataset

    def augment_with_parents(self, dataset):
        parents = get_wdae_parents(dataset["id"])
        parents = [ds.dataset_id for ds in parents]
        dataset["parents"] = parents
        return dataset

    def get(self, request, dataset_id=None):
        user = request.user
        if dataset_id is None:
            selected_genotype_data = \
                self.gpf_instance.get_selected_genotype_data() \
                or self.gpf_instance.get_genotype_data_ids()

            datasets = filter(None, [
                self.gpf_instance.get_wdae_wrapper(genotype_data_id)
                for genotype_data_id in selected_genotype_data
            ])

            # assert all([d is not None for d in datasets]), \
            #     selected_genotype_data

            res = [
                StudyWrapperBase.build_genotype_data_all_datasets(
                    dataset.config
                )
                for dataset in datasets
            ]
            if not self.gpf_instance.get_selected_genotype_data():
                res = sorted(
                    res,
                    key=lambda desc: desc["name"]
                )
            res = [self.augment_accessibility(ds, user) for ds in res]
            res = [self.augment_with_groups(ds) for ds in res]
            res = [self.augment_with_parents(ds) for ds in res]

            return Response({"data": res})
        else:
            dataset = self.gpf_instance.get_wdae_wrapper(dataset_id)
            if dataset:
                dataset_object = Dataset.objects.get(dataset_id=dataset_id)

                if user_has_permission(user, dataset_object):
                    person_set_collection_configs = {
                        psc.id: psc.config_json()
                        for psc in dataset.person_set_collections.values()
                    }
                    res = StudyWrapperBase\
                        .build_genotype_data_group_description(
                            self.gpf_instance,
                            dataset.config,
                            dataset.description,
                            person_set_collection_configs
                        )
                else:
                    res = StudyWrapperBase.build_genotype_data_all_datasets(
                        dataset.config
                    )

                res = self.augment_accessibility(res, user)
                res = self.augment_with_groups(res)
                res = self.augment_with_parents(res)

                return Response({"data": res})
            return Response(
                {"error": "Dataset {} not found".format(dataset_id)},
                status=status.HTTP_404_NOT_FOUND,
            )


class PermissionDeniedPromptView(QueryBaseView):
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
    def get(self, request, dataset_id):
        if dataset_id is None:
            return Response(
                {"error": "No dataset ID given"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        genotype_data_config = \
            self.gpf_instance.get_genotype_data_config(dataset_id)
        if genotype_data_config is None:
            return Response(
                {"error": f"No such dataset {dataset_id}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        has_denovo = genotype_data_config.get("has_denovo", False)

        dataset_details = {
            "hasDenovo": has_denovo,
            "genome": genotype_data_config.genome,
            "chrPrefix": genotype_data_config.chr_prefix,
        }
        return Response(dataset_details)


class DatasetPedigreeView(QueryBaseView):
    def get(self, request, dataset_id, column):
        if dataset_id is None:
            return Response(
                {"error": "No dataset ID given"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        genotype_data = self.gpf_instance.get_genotype_data(dataset_id)

        if genotype_data is None:
            return Response(
                {"error": f"No such dataset {dataset_id}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        values_domain = list(
            map(str, genotype_data.families.ped_df[column].unique())
        )

        return Response(
            {"column_name": column, "values_domain": values_domain}
        )


class DatasetConfigView(DatasetView):
    def get(self, request, dataset_id):
        if dataset_id is None:
            return Response(
                {"error": "No dataset ID given"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        genotype_data = self.gpf_instance.get_genotype_data(dataset_id)

        if genotype_data is None:
            return Response(
                {"error": f"No such dataset {dataset_id}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            self.augment_with_parents(genotype_data.config.to_dict())
        )


class DatasetDescriptionView(DatasetView):
    def post(self, request, dataset_id):
        if not request.user.is_staff:
            return Response(
                {"error": "You have no permission to edit the description."},
                status=status.HTTP_403_FORBIDDEN
            )

        description = request.data.get('description')
        if dataset_id is None:
            return Response(
                {"error": "No dataset ID given."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        genotype_data = self.gpf_instance.get_genotype_data(dataset_id)
        genotype_data.description = description

        return Response(status=status.HTTP_200_OK)
