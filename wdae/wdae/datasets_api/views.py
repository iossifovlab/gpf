from rest_framework.response import Response
from rest_framework import status
from guardian.shortcuts import get_groups_with_perms

from query_base.query_base import QueryBaseView

from .models import Dataset
from groups_api.serializers import GroupSerializer


class DatasetView(QueryBaseView):

    def augment_accessibility(self, dataset, user):
        dataset_object = Dataset.objects.get(dataset_id=dataset['id'])
        dataset['accessRights'] = user.has_perm('datasets_api.view',
                                                dataset_object)
        return dataset

    def augment_with_groups(self, dataset):
        dataset_object = Dataset.objects.get(dataset_id=dataset['id'])
        groups = get_groups_with_perms(dataset_object)
        serializer = GroupSerializer(groups, many=True)
        dataset['groups'] = serializer.data

        return dataset

    def get(self, request, dataset_id=None):
        user = request.user
        if dataset_id is None:
            datasets = self.variants_db.get_all_genotype_data_wrappers()
            res = sorted(list(dataset.get_genotype_data_group_description()
                         for dataset in datasets),
                         key=lambda dataset: dataset['name'] or dataset['id'])

            res = [self.augment_accessibility(ds, user) for ds in res]
            res = [self.augment_with_groups(ds) for ds in res]

            return Response({'data': res})
        else:
            dataset = self.variants_db.get_wdae_wrapper(dataset_id)
            if dataset:
                res = dataset.get_genotype_data_group_description()
                res = self.augment_accessibility(res, user)
                res = self.augment_with_groups(res)
                return Response({'data': res})
            return Response(
                {
                    'error': 'Dataset {} not found'.format(dataset_id)
                },
                status=status.HTTP_404_NOT_FOUND)


class PermissionDeniedPromptView(QueryBaseView):

    def __init__(self):
        super(PermissionDeniedPromptView, self).__init__()

        prompt_filepath = \
            self.gpf_instance.dae_config.gpfjs.permission_denied_prompt_file

        with open(prompt_filepath, "r") as infile:
            self.permission_denied_prompt = infile.read()

    def get(self, request):
        return Response({'data': self.permission_denied_prompt})


class DatasetDetailsView(QueryBaseView):
    def get(self, request, dataset_id):
        if dataset_id is None:
            return Response({
                'error': 'No dataset ID given'
            }, status=status.HTTP_400_BAD_REQUEST)

        genotype_data = self.gpf_instance.get_genotype_data(dataset_id)

        if genotype_data is None:
            return Response({
                'error': f'No such dataset {dataset_id}'
            }, status=status.HTTP_400_BAD_REQUEST)

        dataset_details = \
            {'hasDenovo': genotype_data.has_denovo}
        return Response(dataset_details)
