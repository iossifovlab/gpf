from rest_framework import status
from rest_framework.response import Response
from django.http.response import StreamingHttpResponse

import numpy as np

from query_base.query_base import QueryBaseView


class GeneScoresListView(QueryBaseView):
    def __init__(self):
        super(GeneScoresListView, self).__init__()

    def get(self, request):
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
                    "score": score.id,
                    "desc": score.desc,
                    "bars": score.histogram_bars,
                    "bins": score.histogram_bins,
                    "xscale": score.xscale,
                    "yscale": score.yscale,
                    "range": score.range,
                }
                for score in gene_scores
            ]
        )


class GeneScoresDownloadView(QueryBaseView):
    def __init__(self):
        super(GeneScoresDownloadView, self).__init__()

    def get(self, request, score):
        tsv = self.gpf_instance.get_gene_score(score).to_tsv()

        response = StreamingHttpResponse(tsv, content_type="text/csv")

        response["Content-Disposition"] = "attachment; filename=scores.csv"
        response["Expires"] = "0"
        return response


class GeneScoresGetGenesView(QueryBaseView):
    def __init__(self):
        super(GeneScoresGetGenesView, self).__init__()

    def prepare_data(self, data):
        if "score" not in data:
            raise ValueError("score key not found")
        wname = data["score"]
        if not self.gpf_instance.has_gene_score(wname):
            raise ValueError("unknown gene score")
        if "min" not in data:
            wmin = None
        else:
            wmin = float(data["min"])
        if "max" not in data:
            wmax = None
        else:
            wmax = float(data["max"])
        return self.gpf_instance.get_gene_score(wname).get_genes(
            wmin=wmin, wmax=wmax
        )

    def post(self, request):
        data = self.request.data
        genes = self.prepare_data(data)
        return Response(genes)


class GeneScoresPartitionsView(QueryBaseView):
    def __init__(self):
        super(GeneScoresPartitionsView, self).__init__()

    def post(self, request):
        data = request.data

        assert "score" in data

        score_name = data["score"]

        if not self.gpf_instance.has_gene_score(score_name):
            return Response(status=status.HTTP_404_NOT_FOUND)

        w = self.gpf_instance.get_gene_score(score_name)
        df = w.df

        try:
            wmin = float(data["min"])
        except TypeError:
            wmin = float("-inf")

        try:
            wmax = float(data["max"])
        except TypeError:
            wmax = float("inf")

        total = 1.0 * len(df)
        ldf = df[df[score_name] < wmin]
        rdf = df[df[score_name] >= wmax]
        mdf = df[
            np.logical_and(df[score_name] >= wmin, df[score_name] < wmax)
        ]

        res = {
            "left": {"count": len(ldf), "percent": len(ldf) / total},
            "mid": {"count": len(mdf), "percent": len(mdf) / total},
            "right": {"count": len(rdf), "percent": len(rdf) / total},
        }
        return Response(res)
