'''
Created on Dec 10, 2015

@author: lubo
'''
from __future__ import division
from __future__ import unicode_literals
from builtins import map
from builtins import str
from past.utils import old_div

from rest_framework import views, status
from rest_framework.response import Response
from django.http.response import StreamingHttpResponse

import itertools
import numpy as np

from datasets_api.studies_manager import get_studies_manager

from users_api.authentication import SessionAuthenticationWithoutCSRF
from helpers.dae_query import join_line


class GeneWeightsListView(views.APIView):

    def __init__(self):
        self.weights_loader = get_studies_manager().get_weights_loader()

    def get_gene_weights(self, weights):
        return [
            {
                'weight': weight.name,
                'desc': weight.desc,
                'bars': weight.histogram_bars,
                'bins': weight.histogram_bins,
                'xscale': weight.xscale,
                'yscale': weight.yscale,
                'range': weight.range
            } for weight in weights
        ]

    def get(self, request):
        weights = self.weights_loader.get_weights()
        gene_weights = self.get_gene_weights(weights)

        return Response(gene_weights)


class GeneWeightsDownloadView(views.APIView):

    def __init__(self):
        self.weights_loader = get_studies_manager().get_weights_loader()

    def get(self, request, weight):
        df = self.weights_loader[weight].df
        columns = df.columns.values.tolist()
        m = [[str(getattr(x, col)) for col in columns]
             for x in df.itertuples()]
        m = itertools.chain([columns], m)

        response = StreamingHttpResponse(list(map(join_line, m)),
                                         content_type='text/csv')

        response['Content-Disposition'] = 'attachment; filename=weights.csv'
        response['Expires'] = '0'
        return response


class GeneWeightsGetGenesView(views.APIView):
    authentication_classes = (SessionAuthenticationWithoutCSRF, )

    def __init__(self):
        self.weights_loader = get_studies_manager().get_weights_loader()

    def prepare_data(self, data):
        if 'weight' not in data:
            raise ValueError('weight key not found')
        wname = data['weight']
        if wname not in self.weights_loader:
            raise ValueError('unknown gene weight')
        if 'min' not in data:
            wmin = None
        else:
            wmin = float(data['min'])
        if 'max' not in data:
            wmax = None
        else:
            wmax = float(data['max'])
        return self.weights_loader[wname].get_genes(wmin=wmin, wmax=wmax)

    def post(self, request):
        data = self.request.data
        genes = self.prepare_data(data)
        return Response(genes)


class GeneWeightsPartitionsView(views.APIView):
    authentication_classes = (SessionAuthenticationWithoutCSRF, )

    def __init__(self):
        self.weights_loader = get_studies_manager().get_weights_loader()

    def post(self, request):
        data = request.data

        assert "weight" in data
        assert self.weights_loader is not None

        weight_name = data['weight']

        if weight_name not in self.weights_loader:
            return Response(status=status.HTTP_404_NOT_FOUND)

        w = self.weights_loader[weight_name]
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
        mdf = df[np.logical_and(
            df[weight_name] >= wmin, df[weight_name] < wmax)]

        res = {"left": {"count": len(ldf), "percent": old_div(len(ldf), total)},
               "mid": {"count": len(mdf), "percent": old_div(len(mdf), total)},
               "right": {"count": len(rdf), "percent": old_div(len(rdf), total)}}
        return Response(res)
