'''
Created on Aug 3, 2015

@author: lubo
'''
from __future__ import unicode_literals
from django.http.response import StreamingHttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from datasets_api.studies_manager import get_studies_manager
from datasets_api.permissions import IsDatasetAllowed

from helpers.dae_query import join_line


class StudiesSummariesView(APIView):

    def __init__(self):
        self.common_reports_facade =\
            get_studies_manager().get_common_report_facade()

    def get_studies_summaries(self, common_reports):
        return {
            'columns': [
                'study name',
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
                'transmitted': common_report.get('transmitted', ''),
                'id': common_report.get(
                    'id', common_report.get('study_name', ''))
            } for common_report in common_reports]
        }

    def get(self, request):
        common_reports =\
            self.common_reports_facade.get_all_common_reports()

        studies_summaries = self.get_studies_summaries(common_reports)
        return Response(studies_summaries)


class VariantReportsView(APIView):

    def __init__(self):
        self.common_reports_facade =\
            get_studies_manager().get_common_report_facade()

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
        assert common_report_id

        common_report = self.common_reports_facade.get_common_report(
            common_report_id)

        common_report['is_downloadable'] =\
            IsDatasetAllowed.user_has_permission(
                request.user, common_report_id)

        if common_report:
            return Response(common_report)
        return Response(
            {
                'error': 'Common report {} not found'.format(
                    common_report_id)
            },
            status=status.HTTP_404_NOT_FOUND)


class FamiliesDataDownloadView(APIView):
    def __init__(self):
        self.common_reports_facade =\
            get_studies_manager().get_common_report_facade()

    def to_tsv(self, common_report_id):
        study = get_studies_manager().get_variants_db().get_wdae_wrapper(
            common_report_id)

        data = []
        data.append(['familyId', 'personId', 'dadId', 'momId', 'gender',
                     'status', 'role', 'study'])

        families = list(study.families.values())
        families.sort(key=lambda f: f.family_id)
        for f in families:
            for (o, p) in enumerate(f.members_in_order):
                if p.generated:
                    continue

                row = [
                    p.family_id,
                    p.person_id,
                    p.dad_id,
                    p.mom_id,
                    p.sex,
                    p.status,
                    p.role,
                    study.name,
                ]

                data.append(row)

        return list(map(join_line, data))

    def get(self, request, common_report_id):
        report = self.common_reports_facade.get_common_report(common_report_id)
        if not report:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if not IsDatasetAllowed.user_has_permission(
                request.user, common_report_id):
            return Response(status=status.HTTP_403_FORBIDDEN)

        families_data = self.to_tsv(common_report_id)

        response = StreamingHttpResponse(
            families_data, content_type='text/tsv')

        response['Content-Disposition'] = 'attachment; filename=families.ped'
        response['Expires'] = '0'

        return response
