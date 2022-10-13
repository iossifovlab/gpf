from rest_framework import status
from rest_framework.response import Response
from django.http.response import StreamingHttpResponse

import numpy as np

from query_base.query_base import QueryBaseView


class GeneScoresListView(QueryBaseView):
    """Provides list of all gene scores."""

    def get(self, request):
        """Build list of gene scores and return it."""
        ids = request.query_params.get("ids")
        if ids:
            gene_scores = [
                self.gpf_instance.get_gene_score(gene_score)
                for gene_score in ids.strip().split(",")
            ]
        else:
            gene_scores = self.gpf_instance.get_all_gene_scores()
        return Response(
            [
                {
                    "score": score.score_id,
                    "desc": score.desc,
                    "bars": score.histogram_bars,
                    "bins": score.histogram_bins,
                    "xscale": score.x_scale,
                    "yscale": score.y_scale,
                    "range": score.histogram.range,
                }
                for score in gene_scores
            ]
        )


class GeneScoresDownloadView(QueryBaseView):
    """Serves gene scores download requests."""

    def get(self, _request, score):
        """Serve a gene score download request."""
        tsv = self.gpf_instance.get_gene_score(score).to_tsv()

        response = StreamingHttpResponse(tsv, content_type="text/csv")

        response["Content-Disposition"] = "attachment; filename=scores.csv"
        response["Expires"] = "0"
        return response


class GeneScoresGetGenesView(QueryBaseView):
    """Serves request for list of gene in a gene score range."""

    def prepare_data(self, data):
        """Prepare list of genes that have a gene score in a range."""
        if "score" not in data:
            raise ValueError("score key not found")
        score_name = data["score"]
        if not self.gpf_instance.has_gene_score(score_name):
            raise ValueError(f"unknown gene score {score_name}")
        if "min" not in data:
            score_min = None
        else:
            score_min = float(data["min"])
        if "max" not in data:
            score_max = None
        else:
            score_max = float(data["max"])
        return self.gpf_instance.get_gene_score(score_name).get_genes(
            score_min=score_min, score_max=score_max
        )

    def post(self, request):
        data = request.data
        genes = self.prepare_data(data)
        return Response(genes)


class GeneScoresPartitionsView(QueryBaseView):
    """Serves gene scores partitions request."""

    def post(self, request):
        """Calculate and return gene score partitions."""
        data = request.data

        assert "score" in data

        score_name = data["score"]

        if not self.gpf_instance.has_gene_score(score_name):
            return Response(status=status.HTTP_404_NOT_FOUND)
        if "min" not in data or "max" not in data:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        score = self.gpf_instance.get_gene_score(score_name)
        df = score.df

        try:
            score_min = float(data["min"])
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            score_max = float(data["max"])
        except ValueError:
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
