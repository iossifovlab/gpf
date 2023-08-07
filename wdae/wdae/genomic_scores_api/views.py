from rest_framework.response import Response

from query_base.query_base import QueryBaseView
from dae.genomic_resources.histogram import NumberHistogram


class GenomicScoresView(QueryBaseView):

    def get(self, _request):
        res = []
        for score_id, score in self.gpf_instance.get_genomic_scores():
            if isinstance(score.hist, NumberHistogram):
                res.append({
                    "score": score_id,
                    "desc": score.description,
                    "bars": score.hist.bars,
                    "bins": score.hist.bins,
                    "xscale":
                        "log" if score.hist.config.x_log_scale else "linear",
                    "yscale":
                        "log" if score.hist.config.y_log_scale else "linear",
                    "range": score.hist.view_range,
                    "help": score.help
                })
            else: 
                res.append({
                    "score": score_id,
                    "desc": score.description,
                    "bars": None,
                    "bins": None,
                    "xscale": None,
                    "yscale": None,
                    "range": None,
                    "help": score.help
                })
        return Response(res)
