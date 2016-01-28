'''
Created on Dec 10, 2015

@author: lubo
'''
from rest_framework import views, status
from rest_framework.response import Response
from api.preloaded.register import get_register
import numpy as np


class GeneWeightsListView(views.APIView):

    def get(self, request):
        register = get_register()
        weights = register.get('gene_weights')
        return Response(weights.desc)


class GeneWeightsGetGenesView(views.APIView):

    def prepare_data(self, data):
        register = get_register()
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
        # print("wname={}, wmin={}, wmax={}".format(wname, wmin, wmax))
        return weights.get_genes_by_weight(wname, wmin=wmin, wmax=wmax)

    def post(self, request):
        data = self.request.data
        genes = self.prepare_data(data)
        return Response(genes)


class GeneWeightsPartitionsView(views.APIView):

    def __init__(self):
        self.weights = get_register().get('gene_weights')

    def post(self, request):
        data = request.data

        print("weights partitions request: " +
              str(data))
        assert "weight" in data
        assert self.weights is not None

        weight_name = data['weight']

        if not self.weights.has_weight(weight_name):
            return Response(status=status.HTTP_404_NOT_FOUND)

        df = self.weights.get_weight(weight_name)

        wmin = float(data["min"])
        wmax = float(data["max"])

        total = 1.0 * len(df)

        ldf = df[df < wmin]
        rdf = df[df > wmax]
        mdf = df[np.logical_and(df >= wmin, df <= wmax)]

        res = {"weights": weight_name,
               "wmin": wmin,
               "wmax": wmax,
               "left": {"count": len(ldf), "percent": len(ldf) / total},
               "mid": {"count": len(mdf), "percent": len(mdf) / total},
               "right": {"count": len(rdf), "percent": len(rdf) / total}}
        return Response(res)
