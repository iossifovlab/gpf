from rest_framework.response import Response

from query_base.query_base import QueryBaseView


class GenomicScoresView(QueryBaseView):
    def __init__(self):
        super(GenomicScoresView, self).__init__()

        self.scores_factory = self.gpf_instance._scores_factory

    def get_genomic_scores(self, scores):
        return [
            {
                "score": score.id,
                "desc": score.desc,
                "bars": score.values(),
                "bins": score.get_scores(),
                "xscale": score.xscale,
                "yscale": score.yscale,
                "range": score.range,
                "help": score.help,
            }
            for score in scores
        ]

    def get(self, request):
        scores = self.scores_factory.get_scores()
        genomic_scores = self.get_genomic_scores(scores)

        return Response(genomic_scores)
