'''
Created on Feb 17, 2017

@author: lubo
'''
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
import preloaded


class EnrichmentModelsView(APIView):

    BACKGROUND_MODELS = [
        {'name': 'synonymousBackgroundModel',
         'desc':
         'Background model based on synonymous variants in transmitted'},
        {'name': 'codingLenBackgroundModel',
         'desc': 'Genes coding lenght background model'},
        {'name': 'samochaBackgroundModel',
         'desc': 'Background model described in Samocha et al',
         }
    ]

    COUNTING_MODELS = [
        {'name': 'enrichmentEventsCounting',
         'desc': 'Counting events'},
        {'name': 'enrichmentGeneCounting',
         'desc': 'Counting affected genes'},
    ]

    def get(self, request, dataset_id, enrichment_model_type):
        if enrichment_model_type == 'background':
            return Response(self.BACKGROUND_MODELS)
        if enrichment_model_type == 'counting':
            return Response(self.COUNTING_MODELS)

        return Response(status=status.HTTP_404_NOT_FOUND)


class EnrichmentTestView(APIView):

    def __init__(self):
        register = preloaded.register.get_register()
        self.datasets = register.get('datasets')
        assert self.datasets is not None

        self.datasets_config = self.datasets.get_config()
        self.datasets_factory = self.datasets.get_factory()

    def post(self, request, dataset_id):

        if dataset_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        dataset_desc = self.datasets_config.get_dataset_desc(dataset_id)
        if not dataset_desc:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(dataset_desc)
