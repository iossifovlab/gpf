from rest_framework.response import Response
from rest_framework import status
from guardian.shortcuts import get_groups_with_perms

from query_base.query_base import QueryBaseView

from .models import Dataset
from groups_api.serializers import GroupSerializer
from datasets_api.permissions import get_wdae_parents


class DatasetView(QueryBaseView):

    def augment_accessibility(self, dataset, user):
        dataset_object = Dataset.objects.get(dataset_id=dataset["id"])

        # check normal rights
        dataset["access_rights"] = user.has_perm(
            "datasets_api.view", dataset_object
        )

        # if the dataset is a data group, access to at least one
        # of its studies grants access to the group as well (although limited)
        if not dataset["access_rights"] and dataset.get("studies"):
            for study_id in dataset["studies"]:
                study_perm = user.has_perm(
                    "datasets_api.view",
                    Dataset.objects.get(dataset_id=study_id)
                )
                if study_perm:
                    dataset["access_rights"] = study_perm
                    break

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

            datasets = [
                self.gpf_instance.get_wdae_wrapper(genotype_data_id)
                for genotype_data_id in selected_genotype_data
            ]
            assert all([d is not None for d in datasets]), \
                selected_genotype_data

            res = [
                dataset.build_genotype_data_group_description(
                    self.gpf_instance)
                for dataset in datasets]
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
                res = dataset.build_genotype_data_group_description(
                    self.gpf_instance)
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

        prompt_filepath = (
            self.gpf_instance.dae_config.gpfjs.permission_denied_prompt_file
        )

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

        genotype_data = self.gpf_instance.get_genotype_data(dataset_id)

        if genotype_data is None:
            return Response(
                {"error": f"No such dataset {dataset_id}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        has_denovo = getattr(genotype_data, "has_denovo", False)

        dataset_details = {
            "hasDenovo": has_denovo,
            "genome": genotype_data.config.genome,
            "chrPrefix": genotype_data.config.chr_prefix,
        }
        return Response(dataset_details)
