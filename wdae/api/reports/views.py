'''
Created on Aug 3, 2015

@author: lubo
'''
from rest_framework.views import APIView
from api.precompute import register
from rest_framework.response import Response
from rest_framework import status


class VariantReportsView(APIView):
    def __init__(self):
        self.variant_reports = register.get('variant_reports')

    def get(self, request, study_name):
        report = self.variant_reports[study_name]
        if not report:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response({})
