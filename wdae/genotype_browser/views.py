'''
Created on Feb 6, 2017

@author: lubo
'''
from rest_framework import views, status
from rest_framework.response import Response


from helpers.logger import log_filter, LOGGER
from datasets.config import DatasetConfig


class QueryPreviewView(views.APIView):

    def __init__(self):
        self.datasets = DatasetConfig()

    def post(self, request):
        LOGGER.info(log_filter(request, "query v3 preview request: " +
                               str(request.data)))

        if 'dataset' not in request.data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset_id = request.data['dataset']
        dataset = self.datasets.get_dataset(dataset_id)
        if dataset is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_200_OK)
