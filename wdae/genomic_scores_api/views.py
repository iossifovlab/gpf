from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import os
import os.path
import csv


class GenomicScoresView(APIView):
    def __init__(self):
        self.histograms_data_dir = os.path.join(os.environ['DAE_DB_DIR'],
                                                'genomic_scores/')

    def get(self, request):
        if ('score_id' not in request.query_params):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        genomic_scores = request.query_params['score_id']

        filename = os.path.join(self.histograms_data_dir, genomic_scores)
        bars = []
        bins = []
        with open(filename, 'rb') as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                if len(row[0]) > 0:
                    bars.append(float(row[0]))
                if len(row[1]) > 0:
                    bins.append(float(row[1]))

        result = {
            "id": genomic_scores,
            "bars": bars,
            "bins": bins,
        }

        return Response(result)
