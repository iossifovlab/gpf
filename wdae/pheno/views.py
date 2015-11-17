'''
Created on Nov 16, 2015

@author: lubo
'''
from rest_framework import views
from rest_framework.response import Response


class PhenoReportView(views.APIView):

    def post(self, request):
        return Response()


class PhenoMeasuresView(views.APIView):

    def get(self, request):
        from api.preloaded.register import get_register
        register = get_register()
        measures = register.get('pheno_measures')
        return Response(measures.desc)
