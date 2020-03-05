"""
Created on Feb 6, 2017

@author: lubo
"""
from django.conf.urls import url
from genotype_browser import views

urlpatterns = [
    url(
        r"^/preview$",
        views.QueryPreviewView.as_view(),
        name="genotype_browser_preview",
    ),
    url(
        r"^/preview/variants$",
        views.QueryPreviewVariantsView.as_view(),
        name="genotype_browser_preview_variants",
    ),
    url(
        r"^/download$",
        views.QueryDownloadView.as_view(),
        name="genotype_browser_download",
    ),
]
