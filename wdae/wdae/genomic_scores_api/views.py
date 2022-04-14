from rest_framework.response import Response

from query_base.query_base import QueryBaseView


class GenomicScoresView(QueryBaseView):
    def __init__(self):
        super(GenomicScoresView, self).__init__()

    def get(self, request):
        return Response([
            {
                "score": score.id,
                "desc": score.desc,
                "bars": score.bars,
                "bins": score.bins,
                "xscale": score.xscale,
                "yscale": score.yscale,
                "range": score.range,
                "help": score.help,
            }
            for score in self.gpf_instance.get_genomic_scores()
        ])
