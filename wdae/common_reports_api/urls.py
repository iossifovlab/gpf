'''
Created on May 22, 2017

@author: lubo
'''
from __future__ import unicode_literals

from django.conf.urls import url

from common_reports_api.views import VariantReportsView, \
    FamiliesDataDownloadView, ReportStudies, \
    StudiesSummaries, DenovoStudiesList,\
    TransmittedStudiesList


urlpatterns = [
    url(r'^/variant_reports/(?P<study_name>.+)$',
        VariantReportsView.as_view()),

    url(r'^/families_data/(?P<study_name>.+)$',
        FamiliesDataDownloadView.as_view()),

    url(r'^/report_studies$', ReportStudies.as_view()),

    url(r'^/studies_summaries$', StudiesSummaries.as_view()),

    url(r'^/denovo_studies$', DenovoStudiesList.as_view()),
    url(r'^/transmitted_studies$', TransmittedStudiesList.as_view()),

]
