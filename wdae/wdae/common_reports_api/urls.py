"""
Created on May 22, 2017

@author: lubo
"""
from django.urls import re_path

from common_reports_api import views

urlpatterns = [
    re_path(
        r"^/studies/(?P<common_report_id>.+)$",
        views.VariantReportsView.as_view(),
        name="common_report",
    ),
    re_path(
        r"^/families_data/(?P<dataset_id>.+)$",
        views.FamiliesDataDownloadView.as_view(),
    ),
]
