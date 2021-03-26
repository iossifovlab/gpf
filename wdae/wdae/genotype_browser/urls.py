"""
Created on Feb 6, 2017

@author: lubo
"""
from django.conf.urls import url
from genotype_browser import views

urlpatterns = [
    url(
        r"^/config/?$",
        views.GenotypeBrowserConfigView.as_view(),
        name="genotype_browser_config",
    ),
    url(
        r"^/query/?",
        views.GenotypeBrowserQueryView.as_view(),
        name="genotype_browser_query"
    ),
    url(
        r"^/summary/preview/?$",
        views.QueryPreviewSummaryVariantsView.as_view(),
        name="genotype_browser_summary_variants",
    ),
    url(
        r"^/summary/variants/?$",
        views.QuerySummaryVariantsView.as_view(),
        name="genotype_browser_summary_variants",
    ),
    url(
        r"^/summary/download/?$",
        views.QuerySummaryVariantsDownloadView.as_view(),
        name="genotype_browser_summary_variants",
    ),
]
