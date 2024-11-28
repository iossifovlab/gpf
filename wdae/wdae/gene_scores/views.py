
import numpy as np
from datasets_api.permissions import get_instance_timestamp_etag
from django.http.response import StreamingHttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.http import etag
from query_base.query_base import QueryBaseView
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response


class GeneScoresListView(QueryBaseView):
    """Provides list of all gene scores."""

    @method_decorator(etag(get_instance_timestamp_etag))
    def get(self, request: Request) -> Response:
        """Build list of gene scores and return it."""
        ids = request.query_params.get("ids")
        if ids:
            gene_scores = [
                self.gpf_instance.get_gene_score_desc(gene_score)
                for gene_score in ids.strip().split(",")
            ]
        else:
            gene_scores = self.gpf_instance.get_all_gene_score_descs()
        return Response(
            [
                {
                    "score": score.score_id,
                    "desc": f"{score.name} - {score.description}",
                    "bars": score.hist.bars,
                    "bins": score.hist.bins,
                    "xscale":
                        "log" if score.hist.config.x_log_scale else
                        "linear",
                    "yscale":
                        "log" if score.hist.config.y_log_scale else
                        "linear",
                    "range": score.hist.config.view_range,
                    "help": score.help,
                    "small_values_desc": score.small_values_desc,
                    "large_values_desc": score.large_values_desc,
                }
                for score in gene_scores
            ],
        )


class HistogramView(QueryBaseView):
    """Provides list of all gene scores."""

    @method_decorator(etag(get_instance_timestamp_etag))
    def get(self, request: Request) -> Response:
        """Build list of gene scores and return it."""
        ids = request.query_params.get("ids")
        if ids:
            gene_scores = [
                self.gpf_instance.get_gene_score_desc(gene_score)
                for gene_score in ids.strip().split(",")
            ]
        else:
            gene_scores = self.gpf_instance.get_all_gene_score_descs()
        return Response(
            [
                {
                    "score": score.score_id,
                    "desc": f"{score.name} - {score.description}",
                    "histogram": score.hist.to_dict(),
                    "help": score.help,
                    "small_values_desc": score.small_values_desc,
                    "large_values_desc": score.large_values_desc,
                }
                for score in gene_scores
            ],
        )


class GeneScoresDownloadView(QueryBaseView):
    """Serves gene scores download requests."""

    def get(self, _request: Request, score: str) -> Response:
        """Serve a gene score download request."""
        score_desc = self.gpf_instance.get_gene_score_desc(score)
        gene_score = score_desc.resource_id
        tsv = self.gpf_instance.get_gene_score(gene_score).to_tsv(score)

        response = StreamingHttpResponse(tsv, content_type="text/csv")

        response["Content-Disposition"] = "attachment; filename=scores.csv"
        response["Expires"] = "0"
        return response


class GeneScoresPartitionsView(QueryBaseView):
    """Serves gene scores partitions request."""

    def post(self, request: Request) -> Response:
        """Calculate and return gene score partitions."""
        data = request.data

        assert "score" in data

        score_name = data["score"]

        if not self.gpf_instance.has_gene_score(score_name):
            return Response(status=status.HTTP_404_NOT_FOUND)
        if "min" not in data or "max" not in data:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        score_desc = self.gpf_instance.get_gene_score_desc(score_name)
        gene_score = self.gpf_instance.get_gene_score(score_desc.resource_id)
        df = gene_score.get_score_df(score_name)

        try:
            score_min = float(data["min"])
        except (ValueError, TypeError):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            score_max = float(data["max"])
        except (ValueError, TypeError):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        total = 1.0 * len(df)

        ldf = df[df[score_name] < score_min]
        rdf = df[df[score_name] > score_max]
        mdf = df[
            np.logical_and(
                df[score_name] >= score_min,
                df[score_name] <= score_max)
        ]

        res = {
            "left": {"count": len(ldf), "percent": len(ldf) / total},
            "mid": {"count": len(mdf), "percent": len(mdf) / total},
            "right": {"count": len(rdf), "percent": len(rdf) / total},
        }
        return Response(res)
