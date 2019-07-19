'''
Created on Feb 6, 2017

@author: lubo
'''
from __future__ import unicode_literals
from django.conf.urls import url
from genotype_browser import views

urlpatterns = [
    url(r'^/preview$',
        views.QueryPreviewView.as_view(),
        name="genotype_browser_preview"),

    url(r'^/download$',
        views.QueryDownloadView.as_view(),
        name="genotype_browser_download"),

]
