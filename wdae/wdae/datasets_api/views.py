'''
Created on Jan 20, 2017

@author: lubo
'''
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from guardian.shortcuts import get_groups_with_perms

from .studies_manager import get_studies_manager
from .models import Dataset
from groups_api.serializers import GroupSerializer


class DatasetView(APIView):

    def __init__(self, variants_db=None):
        # assert self.datasets is not None

        if variants_db is None:
            variants_db = get_studies_manager()\
                .get_variants_db()
        self.variants_db = variants_db

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
            datasets = self.variants_db.get_all_wrappers()
            res = sorted(list(dataset.get_dataset_description()
                         for dataset in datasets),
                         key=lambda dataset: dataset['name'])

            res = [self.augment_accessibility(ds, user) for ds in res]
            res = [self.augment_with_groups(ds) for ds in res]
            return Response({'data': res})
        else:
            dataset = self.variants_db.get_wdae_wrapper(dataset_id)
            if dataset:
                res = dataset.get_dataset_description()
                res = self.augment_accessibility(res, user)
                res = self.augment_with_groups(res)
                return Response({'data': res})
            return Response(
                {
                    'error': 'Dataset {} not found'.format(dataset_id)
                },
                status=status.HTTP_404_NOT_FOUND)


class PermissionDeniedPromptView(APIView):

    def __init__(self):
        filepath = get_studies_manager().get_permission_denied_prompt()
        if filepath:
            assert os.path.exists(filepath)
            with open(filepath, 'r') as prompt_file:
                self.permission_denied_prompt = prompt_file.read()
        else:
            self.permission_denied_prompt = \
                ('This is a default permission denied prompt.'
                 ' Please log in or register.')

    def get(self, request):
        return Response({'data': self.permission_denied_prompt})
