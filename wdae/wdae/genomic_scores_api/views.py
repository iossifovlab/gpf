from typing import Optional
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request

from query_base.query_base import QueryBaseView
from dae.genomic_resources.histogram import NumberHistogram


class GenomicScoresView(QueryBaseView):
    """View for genomic scores database for the instance."""

    def get(self, _request: Request) -> Response:
        """List all genomic scores used by the GPF instance."""
        res = []
        for score_id, score in self.gpf_instance.get_genomic_scores():
            if isinstance(score.hist, NumberHistogram):
                res.append({
                    "score": score_id,
                    "name": score.name,
                    "desc": score.name,
                    "bars": score.hist.bars,
                    "bins": score.hist.bins,
                    "xscale":
                        "log" if score.hist.config.x_log_scale else "linear",
                    "yscale":
                        "log" if score.hist.config.y_log_scale else "linear",
                    "range": score.hist.view_range,
                    "help": score.description,
                    "small_values_desc": score.small_values_desc,
                    "large_values_desc": score.large_values_desc,
                })
            else:
                res.append({
                    "score": score_id,
                    "name": score.name,
                    "desc": score.name,
                    "bars": None,
                    "bins": None,
                    "xscale": None,
                    "yscale": None,
                    "range": None,
                    "help": score.description,
                    "small_values_desc": None,
                    "large_values_desc": None,
                })
        return Response(res)


class GenomicScoreDescsView(QueryBaseView):
    """View for accessing inner genomic scores data from federations."""

    def get(
        self, _request: Request, score_id: Optional[str] = None
    ) -> Response:
        """Convert all genomic score descs into a JSON list."""
        res = []
        if score_id is not None:
            if not self.gpf_instance.has_genomic_score(score_id):
                return Response(status=status.HTTP_404_NOT_FOUND)
            scores = [
                (score_id, self.gpf_instance.get_genomic_score(score_id))
            ]
        else:
            scores = self.gpf_instance.get_genomic_scores()

        for _, score in scores:
            res.append(score.to_json())

        return Response(res)
