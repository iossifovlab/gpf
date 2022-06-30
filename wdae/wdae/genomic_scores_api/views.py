from rest_framework.response import Response

from query_base.query_base import QueryBaseView


class GenomicScoresView(QueryBaseView):
    def __init__(self):
        super(GenomicScoresView, self).__init__()

    def get(self, request):
        return Response([
            {
                "score": score_id,
                # "desc": score.desc,
                "bars": score.bars,
                "bins": score.bins,
                "xscale": score.x_scale,
                "yscale": score.y_scale,
                "range": score.range,
                # "help": score.help,
            }
            for score_id, score in self.gpf_instance.get_genomic_scores()
        ])
