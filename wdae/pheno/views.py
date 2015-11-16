'''
Created on Nov 16, 2015

@author: lubo
'''
from rest_framework import views
from rest_framework.response import Response


class PhenoReportView(views.APIView):

    def post(self, request):
        return Response()
