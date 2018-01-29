'''
Created on Jan 20, 2017

@author: lubo
'''
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from guardian.shortcuts import get_groups_with_perms
from datasets_api.models import Dataset
from groups_api.serializers import GroupSerializer
import preloaded
from DAE import StatusMixin


class DatasetView(APIView):

    def __init__(self):
        register = preloaded.register
        self.datasets = register.get('datasets')
        assert self.datasets is not None

        self.datasets_config = self.datasets.get_config()
        self.datasets_factory = self.datasets.get_factory()

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

    def augment_status_filter(selfs, dataset):
        dataset['statusFilter'] = list(StatusMixin.AFFECTED_MAPPING.keys())
        return dataset

    def get(self, request, dataset_id=None):
        user = request.user
        if dataset_id is None:
            res = self.datasets_factory.get_description_datasets()

            res = [self.augment_accessibility(ds, user) for ds in res]
            res = [self.augment_with_groups(ds) for ds in res]
            res = [self.augment_status_filter(ds) for ds in res]
            return Response({'data': res})
        else:
            res = self.datasets_factory.get_description_dataset(dataset_id)
            if res:
                res = self.augment_accessibility(res, user)
                res = self.augment_with_groups(res)
                res = self.augment_status_filter(res)
                return Response({'data': res})
            return Response(
                {
                    'error': 'Dataset {} not found'.format(dataset_id)
                },
                status=status.HTTP_404_NOT_FOUND)
