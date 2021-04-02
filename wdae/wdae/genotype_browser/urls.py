"""
Created on Feb 6, 2017

@author: lubo
"""
from django.conf.urls import url
from genotype_browser import views

urlpatterns = [
    url(
        r"^/query/?",
        views.GenotypeBrowserQueryView.as_view(),
        name="genotype_browser_query"
    ),
]
