"""
Created on Feb 17, 2017

@author: lubo
"""
from django.urls import re_path
from . import views


urlpatterns = [
    re_path(
        r"^/models/(?P<dataset_id>.+)",
        views.EnrichmentModelsView.as_view(),
        name="enrichment_models",
    ),
    re_path(
        r"^/test/?$",
        views.EnrichmentTestView.as_view(),
        name="enrichment_test"
    ),
]
