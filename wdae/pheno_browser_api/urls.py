'''
Created on Apr 21, 2017

@author: lubo
'''
from __future__ import unicode_literals
from django.conf.urls import url
from pheno_browser_api import views


urlpatterns = [
    url(r'^/instruments$',
        views.PhenoInstrumentsView.as_view(),
        name="pheno_browser_instruments"),
    url(r'^/measures$',
        views.PhenoMeasuresView.as_view(),
        name="pheno_browser_measures"),
    url(r'^/download$',
        views.PhenoMeasuresDownload.as_view(),
        name="pheno_browser_download"),
]
