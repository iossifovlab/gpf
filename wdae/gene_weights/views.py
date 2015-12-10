'''
Created on Dec 10, 2015

@author: lubo
'''
from rest_framework import views, status
from rest_framework.response import Response
from api.preloaded.register import get_register


class GeneWeightsListView(views.APIView):

    def get(self, request):
        register = get_register()
        weights = register.get('gene_weights')
        return Response(weights.desc)
