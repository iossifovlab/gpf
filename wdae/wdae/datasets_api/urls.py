"""
Created on Jan 20, 2017

@author: lubo
"""
from django.conf.urls import url
from . import views


urlpatterns = [
    url(
        r"^/denied_prompt$",
        views.PermissionDeniedPromptView.as_view(),
        name="denied_prompt",
    ),
    url(
        r"^/details/(?P<dataset_id>.+)$",
        views.DatasetDetailsView.as_view(),
        name="dataset_details",
    ),
    url(r"^/(?P<dataset_id>.+)$", views.DatasetView.as_view(), name="dataset"),
    url(r"^$", views.DatasetView.as_view(), name="dataset_all"),
]
