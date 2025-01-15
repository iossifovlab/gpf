
from datasets_api.permissions import get_instance_timestamp_etag
from django.utils.decorators import method_decorator
from django.views.decorators.http import etag
from query_base.query_base import QueryBaseView
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response


class GenomicScoresView(QueryBaseView):
    """View for genomic scores database for the instance."""

    @method_decorator(etag(get_instance_timestamp_etag))
    def get(self, _request: Request) -> Response:
        """List all genomic scores used by the GPF instance."""
        res = []
        registry = self.gpf_instance.genomic_scores
        for score_id, score in registry.get_scores():
            res.append({
                "score": score_id,
                "desc": score.description,
                "histogram": score.hist.to_dict(),
                "help": score.help,
                "small_values_desc": score.small_values_desc,
                "large_values_desc": score.large_values_desc,
            })

        return Response(res)


class GenomicScoreDescsView(QueryBaseView):
    """View for accessing inner genomic scores data from federations."""

    @method_decorator(etag(get_instance_timestamp_etag))
    def get(
        self, _request: Request, score_id: str | None = None,
    ) -> Response:
        """Convert all genomic score descs into a JSON list."""
        registry = self.gpf_instance.genomic_scores

        res = []
        if score_id is not None:
            if score_id not in registry:
                return Response(status=status.HTTP_404_NOT_FOUND)
            scores = [
                (score_id, registry[score_id]),
            ]
        else:
            scores = registry.get_scores()

        for _, score in scores:
            res.append(score.to_json())

        return Response(res)
