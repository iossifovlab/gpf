'''
Created on Jan 20, 2017

@author: lubo
'''
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datasets_api.models import Dataset
from guardian.utils import get_anonymous_user

import preloaded


class DatasetView(APIView):

    def __init__(self):
        register = preloaded.register.get_register()
        self.datasets = register.get('datasets')
        assert self.datasets is not None

        self.datasets_config = self.datasets.get_config()
        self.datasets_factory = self.datasets.get_factory()

    def augment_accessibility(self, dataset, user):
        datasetObject = Dataset.objects.get(dataset_id=dataset['id'])
        dataset['accessRights'] = user.has_perm('datasets_api.view', datasetObject) or\
                                  get_anonymous_user().has_perm('datasets_api.view', datasetObject)

        return dataset

    def get(self, request, dataset_id=None):
        user = request.user

        if dataset_id is None:
            res = self.datasets_factory.get_description_datasets()
            res = [self.augment_accessibility(ds, user) for ds in res]
            return Response({'data': res})
        else:
            res = self.datasets_factory.get_description_dataset(dataset_id)
            if res:
                res = self.augment_accessibility(res, user)
                return Response({'data': res})
            return Response(
                {
                    'error': 'Dataset {} not found'.format(dataset_id)
                },
                status=status.HTTP_404_NOT_FOUND)
