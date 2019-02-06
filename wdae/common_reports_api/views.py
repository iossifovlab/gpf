'''
Created on Aug 3, 2015

@author: lubo
'''
from __future__ import unicode_literals
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

import preloaded


class StudiesSummariesView(APIView):

    def __init__(self):
        register = preloaded.register
        self.common_reports = register.get('common_reports')
        assert self.common_reports is not None

        self.common_reports_facade = self.common_reports.get_facade()

    def get_studies_summaries(self, common_reports):
        return {
            'columns': [
                'study name',
                'description',
                'phenotype',
                'study type',
                'study year',
                'PubMed',
                'families',
                'number of probands',
                'number of siblings',
                'denovo',
                'transmitted'
            ],
            'summaries': [{
                'study name': common_report.get('study_name', ''),
                'description': common_report.get('study_description', ''),
                'phenotype': common_report.get('phenotype', ''),
                'study type': common_report.get('study_type', ''),
                'study year': common_report.get('study_year', ''),
                'PubMed': common_report.get('pub_med', ''),
                'families': common_report.get('families', ''),
                'number of probands':
                    common_report.get('number_of_probands', ''),
                'number of siblings':
                    common_report.get('number_of_siblings', ''),
                'denovo': common_report.get('denovo', ''),
                'transmitted': common_report.get('transmitted', '')
            } for common_report in common_reports]
        }

    def get(self, request):
        common_reports =\
            self.common_reports_facade.get_all_common_reports()

        studies_summaries = self.get_studies_summaries(common_reports)
        return Response(studies_summaries)


class VariantReportsView(APIView):

    def __init__(self):
        register = preloaded.register
        self.common_reports = register.get('common_reports')
        assert self.common_reports is not None

        self.common_reports_facade = self.common_reports.get_facade()

    def get_studies_info(self, common_reports):
        return [
            {
                'id': common_report.get(
                    'id', common_report.get('study_name', '')),
                'study_name': common_report.get('study_name', ''),
                'study_description': common_report.get('study_description', '')
            } for common_report in common_reports
        ]

    def get(self, request, common_report_id=None):
        if common_report_id is None:
            common_reports =\
                self.common_reports_facade.get_all_common_reports()

            studies = self.get_studies_info(common_reports)

            return Response({'report_studies': studies})
        else:
            common_report = self.common_reports_facade.get_common_report(
                common_report_id)

            if common_report:
                return Response(common_report)
            return Response(
                {
                    'error': 'Common report {} not found'.format(
                        common_report_id)
                },
                status=status.HTTP_404_NOT_FOUND)
