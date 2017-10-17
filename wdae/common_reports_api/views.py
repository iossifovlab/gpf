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
from common_reports_api.studies import get_denovo_studies_names,\
    get_transmitted_studies_names
import itertools


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


class ReportStudies(APIView):

    def get(self, _request):
        seen = set()
        names = []
        for name in itertools.chain(get_denovo_studies_names(),
                                    get_transmitted_studies_names()):
            print(name)
            if name[0] in seen:
                continue
            names.append(name)
            seen.add(name[0])

        return Response({"report_studies": names})


class StudiesSummaries(APIView):
    def __init__(self):
        self.studies_summaries = register.get('studies_summaries')

    def get(self, request):
        return Response(self.studies_summaries.summaries)


class DenovoStudiesList(APIView):

    def get(self, request):
        r = get_denovo_studies_names()
        return Response({"denovo_studies": r})


class TransmittedStudiesList(APIView):

    def get(self, request):
        r = get_transmitted_studies_names()
        return Response({"transmitted_studies": r})
