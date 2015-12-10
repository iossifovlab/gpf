'''
Created on Dec 10, 2015

@author: lubo
'''
from rest_framework import views
from rest_framework.response import Response
from api.preloaded.register import get_register


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
