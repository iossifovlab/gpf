'''
Created on Jan 20, 2017

@author: lubo
'''
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from datasets.config import DatasetsConfig


class DatasetView(APIView):

    def __init__(self):
        self.dataset_config = DatasetsConfig()

    def get(self, request, dataset_id=None):

        print("dataset view get called...")

        if dataset_id is None:
            res = self.dataset_config.get_datasets()
            return Response({'data': res})
        res = self.dataset_config.get_dataset(dataset_id)
        if res:
            return Response({'data': res})
        return Response({'error': 'Dataset {} not found'.format(dataset_id)},
                        status=status.HTTP_404_NOT_FOUND)
