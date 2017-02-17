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

    def get(self, request, dataset_id=None):
        if dataset_id is None:
            res = self.datasets_config.get_datasets()
            return Response({'data': res})
        res = self.datasets_config.get_dataset_desc(dataset_id)
        if res:
            return Response({'data': res})
        return Response({'error': 'Dataset {} not found'.format(dataset_id)},
                        status=status.HTTP_404_NOT_FOUND)
