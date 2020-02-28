"""
Created on May 22, 2017

@author: lubo
"""
from django.conf.urls import url

from common_reports_api import views

urlpatterns = [
    url(
        r"^/studies/(?P<common_report_id>.+)$",
        views.VariantReportsView.as_view(),
        name="common_report",
    ),
    url(
        r"^/families_data/(?P<common_report_id>.+)$",
        views.FamiliesDataDownloadView.as_view(),
    ),
]
