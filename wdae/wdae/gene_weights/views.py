from rest_framework import status
from rest_framework.response import Response
from django.http.response import StreamingHttpResponse

import numpy as np

from query_base.query_base import QueryBaseView


class GeneWeightsListView(QueryBaseView):
    def __init__(self):
        super(GeneWeightsListView, self).__init__()

    def get(self, request):
        ids = request.query_params.get("ids")
        if ids:
            gene_weights = [
                self.gpf_instance.get_gene_weight(gene_weight)
                for gene_weight in ids.strip().split(",")
            ]
        else:
            gene_weights = self.gpf_instance.get_all_gene_weights()
        return Response(
            [
                {
                    "weight": weight.id,
                    "desc": weight.desc,
                    "bars": weight.histogram_bars,
                    "bins": weight.histogram_bins,
                    "xscale": weight.xscale,
                    "yscale": weight.yscale,
                    "range": weight.range,
                }
                for weight in gene_weights
            ]
        )


class GeneWeightsDownloadView(QueryBaseView):
    def __init__(self):
        super(GeneWeightsDownloadView, self).__init__()

    def get(self, request, weight):
        tsv = self.gpf_instance.get_gene_weight(weight).to_tsv()

        response = StreamingHttpResponse(tsv, content_type="text/csv")

        response["Content-Disposition"] = "attachment; filename=weights.csv"
        response["Expires"] = "0"
        return response


class GeneWeightsGetGenesView(QueryBaseView):
    def __init__(self):
        super(GeneWeightsGetGenesView, self).__init__()

    def prepare_data(self, data):
        if "weight" not in data:
            raise ValueError("weight key not found")
        wname = data["weight"]
        if not self.gpf_instance.has_gene_weight(wname):
            raise ValueError("unknown gene weight")
        if "min" not in data:
            wmin = None
        else:
            wmin = float(data["min"])
        if "max" not in data:
            wmax = None
        else:
            wmax = float(data["max"])
        return self.gpf_instance.get_gene_weight(wname).get_genes(
            wmin=wmin, wmax=wmax
        )

    def post(self, request):
        data = self.request.data
        genes = self.prepare_data(data)
        return Response(genes)


class GeneWeightsPartitionsView(QueryBaseView):
    def __init__(self):
        super(GeneWeightsPartitionsView, self).__init__()

    def post(self, request):
        data = request.data

        assert "weight" in data

        weight_name = data["weight"]

        if not self.gpf_instance.has_gene_weight(weight_name):
            return Response(status=status.HTTP_404_NOT_FOUND)

        w = self.gpf_instance.get_gene_weight(weight_name)
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
        ldf = df[df[weight_name] < wmin]
        rdf = df[df[weight_name] >= wmax]
        mdf = df[
            np.logical_and(df[weight_name] >= wmin, df[weight_name] < wmax)
        ]

        res = {
            "left": {"count": len(ldf), "percent": len(ldf) / total},
            "mid": {"count": len(mdf), "percent": len(mdf) / total},
            "right": {"count": len(rdf), "percent": len(rdf) / total},
        }
        return Response(res)
