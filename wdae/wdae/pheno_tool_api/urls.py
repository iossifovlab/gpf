"""
Created on Nov 16, 2015

@author: lubo
"""
from django.conf.urls import url
from pheno_tool_api import views


urlpatterns = [
    url(r"^/?$", views.PhenoToolView.as_view(), name="pheno_tool"),
    url(
        r"^/download/?$",
        views.PhenoToolDownload.as_view(),
        name="pheno_tool_download",
    ),
    url(
        r"^/persons/?$",
        views.PhenoToolPersons.as_view(),
        name="pheno_tool_persons"
    ),
    url(
        r"^/persons_values/?$",
        views.PhenoToolPersonsValues.as_view(),
        name="pheno_tool_persons_values"
    ),
    url(
        r"^/measure/?$",
        views.PhenoToolMeasure.as_view(),
        name="pheno_tool_measure"
    ),
    url(
        r"^/measures/?$",
        views.PhenoToolMeasures.as_view(),
        name="pheno_tool_measures"
    ),
    url(
        r"^/measure_values/?$",
        views.PhenoToolMeasureValues.as_view(),
        name="pheno_tool_measure_values"
    ),
    url(
        r"^/values/?$",
        views.PhenoToolValues.as_view(),
        name="pheno_tool_values"
    ),
    url(
        r"^/instruments/?$",
        views.PhenoToolInstruments.as_view(),
        name="pheno_tool_instruments"
    ),
    url(
        r"^/instrument_values/?$",
        views.PhenoToolInstrumentValues.as_view(),
        name="pheno_tool_instrument_values"
    ),
]
