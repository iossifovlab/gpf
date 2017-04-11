'''
Created on Jan 20, 2017

@author: lubo
'''
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import preloaded


class DatasetView(APIView):

    def __init__(self):
        register = preloaded.register.get_register()
        self.datasets = register.get('datasets')
        assert self.datasets is not None

        self.datasets_config = self.datasets.get_config()
        self.datasets_factory = self.datasets.get_factory()

    def augment_accessibility(self, dataset, user):
        access_rights = False
        if dataset['visibility'] == 'ALL':
            access_rights = True
        if dataset['visibility'] == 'AUTHENTICATED' \
                and user.is_authenticated():
            access_rights = True
        if dataset['visibility'] == 'STAFF' \
                and user.is_staff:
            access_rights = True
        dataset['accessRights'] = access_rights
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
