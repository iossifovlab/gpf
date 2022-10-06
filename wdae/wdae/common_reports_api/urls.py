"""
Created on May 22, 2017

@author: lubo
"""
from django.urls import re_path

from common_reports_api import views

urlpatterns = [
    re_path(
        r"^/studies/(?P<common_report_id>.+)/full$",
        views.VariantReportsFullView.as_view(),
        name="common_report_full",
    ),
    re_path(
        r"^/studies/(?P<common_report_id>.+)$",
        views.VariantReportsView.as_view(),
        name="common_report",
    ),
    re_path(
        r"^/family_counters$",
        views.FamilyCounterListView.as_view(),
        name="family_counter_list",
    ),
    re_path(
        r"^/family_counters/download$",
        views.FamilyCounterDownloadView.as_view(),
        name="family_counter_list",
    ),
    re_path(
        r"^/families_data/download$",
        views.FamiliesDataTagDownload.as_view(),
    ),
    re_path(
        r"^/families_data/(?P<dataset_id>.+)$",
        views.FamiliesDataDownloadView.as_view(),
    ),
]
