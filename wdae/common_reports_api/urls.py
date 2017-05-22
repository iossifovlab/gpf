'''
Created on May 22, 2017

@author: lubo
'''

from django.conf.urls import url

from common_reports_api.views import VariantReportsView, \
    FamiliesDataDownloadView


urlpatterns = [
    url(r'^/variant_reports/(?P<study_name>.+)$',
        VariantReportsView.as_view()),

    url(r'^/families_data/(?P<study_name>.+)$',
        FamiliesDataDownloadView.as_view()),

]
