from rest_framework.views import APIView
from rest_framework.response import Response

from datasets_api.studies_manager import get_studies_manager


class GenomicScoresView(APIView):

    def __init__(self):
        self.scores_factory = get_studies_manager().get_scores_factory()

    def get_genomic_scores(self, scores):
        return [
            {
                'score': score.id,
                'desc': score.desc,
                'bars': score.values(),
                'bins': score.get_scores(),
                'xscale': score.xscale,
                'yscale': score.yscale,
                'range': score.range,
                'help': score.help
            } for score in scores
        ]

    def get(self, request):
        scores = self.scores_factory.get_scores()
        genomic_scores = self.get_genomic_scores(scores)

        return Response(genomic_scores)
