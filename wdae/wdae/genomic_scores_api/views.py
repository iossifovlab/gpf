from rest_framework.response import Response

from query_base.query_base import QueryBaseView


class GenomicScoresView(QueryBaseView):

    def get(self, _request):
        return Response([
            {
                "score": score_id,
                "desc": score.description,
                "bars": score.hist.bars,
                "bins": score.hist.bins,
                "xscale": score.hist.x_scale,
                "yscale": score.hist.y_scale,
                "range": score.hist.range,
                # "help": score.help,
            }
            for score_id, score in self.gpf_instance.get_genomic_scores()
        ])
