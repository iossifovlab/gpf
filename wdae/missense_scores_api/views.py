from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import numpy as np
import preloaded


class MissenseScoresView(APIView):
    def __init__(self):
        register = preloaded.register
        self.datasets = register.get('datasets')
        assert self.datasets is not None

        self.datasets_config = self.datasets.get_config()
        self.datasets_factory = self.datasets.get_factory()

    def get(self, request):
        if ('dataset_id' not in request.query_params
                or 'score_id' not in request.query_params):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        dataset_id = request.query_params['dataset_id']
        missense_score = request.query_params['score_id']

        dataset = self.datasets_factory.get_dataset(dataset_id)
        if dataset:
            scores = [float(var.atts[missense_score])
                      for var in dataset.get_variants()
                      if missense_score in var.atts and
                      var.atts[missense_score] != '.' and
                      len(var.atts[missense_score]) > 0]
            bars, bins = np.histogram(scores, 150)

            result = {
                "id": missense_score,
                "min": min(scores),
                "max": max(scores),
                "bars": bars,
                "bins": bins,
            }

            return Response(result)
        else:
            return Response({
                'error': 'Dataset {} not found'.format(dataset_id)
                }, status=status.HTTP_404_NOT_FOUND)
