'''
Created on Aug 3, 2015

@author: lubo
'''
from django.http.response import StreamingHttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from precompute import register
from common_reports_api.families import FamiliesDataCSV
from common_reports_api.serializers import StudyVariantReportsSerializer


class VariantReportsView(APIView):
    def __init__(self):
        self.variant_reports = register.get('variant_reports')

    def get(self, request, study_name):
        report = self.variant_reports[study_name]
        if not report:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = StudyVariantReportsSerializer(report)
        return Response(serializer.data)


class FamiliesDataDownloadView(APIView):
    def __init__(self):
        self.variant_reports = register.get('variant_reports')

    def get(self, request, study_name):
        report = self.variant_reports[study_name]
        if not report:
            return Response(status=status.HTTP_404_NOT_FOUND)

        families_data = FamiliesDataCSV(report.studies)
        response = StreamingHttpResponse(
            families_data.serialize(),
            content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=families.csv'
        response['Expires'] = '0'

        return response
