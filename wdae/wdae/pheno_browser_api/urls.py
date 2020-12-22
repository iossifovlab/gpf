"""
Created on Apr 21, 2017

@author: lubo
"""
from django.conf.urls import url
from pheno_browser_api import views


urlpatterns = [
    url(
        r"^/config/?$",
        views.PhenoConfigView.as_view(),
        name="pheno_browser_config",
    ),
    url(
        r"^/instruments/?$",
        views.PhenoInstrumentsView.as_view(),
        name="pheno_browser_instruments",
    ),
    url(
        r"^/measures_info/?$",
        views.PhenoMeasuresInfoView.as_view(),
        name="pheno_browser_measures_info",
    ),
    url(
        r"^/measures/?$",
        views.PhenoMeasuresView.as_view(),
        name="pheno_browser_measures",
    ),
    url(
        r"^/measure_description/?$",
        views.PhenoMeasureDescriptionView.as_view(),
        name="pheno_browser_measure_description",
    ),
    url(
        r"^/download/?$",
        views.PhenoMeasuresDownload.as_view(),
        name="pheno_browser_download",
    ),
]
