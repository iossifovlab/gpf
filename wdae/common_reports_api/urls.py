'''
Created on May 22, 2017

@author: lubo
'''
from __future__ import unicode_literals
from django.conf.urls import url

from common_reports_api import views

urlpatterns = [
    url(r'^$',
        views.StudiesSummariesView.as_view(),
        name="common_reports_all"),
    url(r'^/studies/(?P<common_report_id>.+)$',
        views.VariantReportsView.as_view(),
        name="common_report"),
    url(r'^/studies$',
        views.VariantReportsView.as_view(),
        name="studies"),
]
