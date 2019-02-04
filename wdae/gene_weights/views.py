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
from preloaded import register
import numpy as np
from users_api.authentication import SessionAuthenticationWithoutCSRF
# from query_variants import join_line
from helpers.dae_query import join_line
import itertools


class GeneWeightsListView(views.APIView):

    def get(self, request):
        weights = register.get('gene_weights')
        return Response(weights.desc)


class GeneWeightsDownloadView(views.APIView):

    def get(self, request, weight):
        weights = register.get('gene_weights')
        df = weights.get_weight(weight).df
        columns = df.columns.values.tolist()
        m = [[str(getattr(x, col)) for col in columns] for x in df.itertuples()]
        m = itertools.chain([columns], m)

        response = StreamingHttpResponse(list(map(join_line, m)),
                                         content_type='text/csv')

        response['Content-Disposition'] = 'attachment; filename=weights.csv'
        response['Expires'] = '0'
        return response


class GeneWeightsGetGenesView(views.APIView):
    authentication_classes = (SessionAuthenticationWithoutCSRF, )

    def prepare_data(self, data):
        weights = register.get('gene_weights')
        if 'weight' not in data:
            raise ValueError('weight key not found')
        wname = data['weight']
        if not weights.has_weight(wname):
            raise ValueError('unknown gene weight')
        if 'min' not in data:
            wmin = None
        else:
            wmin = float(data['min'])
        if 'max' not in data:
            wmax = None
        else:
            wmax = float(data['max'])
        return weights.get_genes_by_weight(
            wname, wmin=wmin, wmax=wmax)

    def post(self, request):
        data = self.request.data
        genes = self.prepare_data(data)
        return Response(genes)


class GeneWeightsPartitionsView(views.APIView):
    authentication_classes = (SessionAuthenticationWithoutCSRF, )

    def __init__(self):
        self.weights = register.get('gene_weights')

    def post(self, request):
        data = request.data

        assert "weight" in data
        assert self.weights is not None

        weight_name = data['weight']

        if not self.weights.has_weight(weight_name):
            return Response(status=status.HTTP_404_NOT_FOUND)

        w = self.weights.get_weight(weight_name)
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
