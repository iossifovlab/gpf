from django.urls import re_path
from pheno_tool_api import views


urlpatterns = [
    re_path(r"^/?$", views.PhenoToolView.as_view(), name="pheno_tool"),
    re_path(
        r"^/download/?$",
        views.PhenoToolDownload.as_view(),
        name="pheno_tool_download",
    ),
    re_path(
        r"^/persons/?$",
        views.PhenoToolPersons.as_view(),
        name="pheno_tool_persons"
    ),
    re_path(
        r"^/persons_values/?$",
        views.PhenoToolPersonsValues.as_view(),
        name="pheno_tool_persons_values"
    ),
    re_path(
        r"^/measure/?$",
        views.PhenoToolMeasure.as_view(),
        name="pheno_tool_measure"
    ),
    re_path(
        r"^/measures/?",
        views.PhenoToolMeasures.as_view(),
        name="pheno_tool_measures"
    ),
    re_path(
        r"^/measure_values/?$",
        views.PhenoToolMeasureValues.as_view(),
        name="pheno_tool_measure_values"
    ),
    re_path(
        r"^/values/?$",
        views.PhenoToolValues.as_view(),
        name="pheno_tool_values"
    ),
    re_path(
        r"^/instruments/?$",
        views.PhenoToolInstruments.as_view(),
        name="pheno_tool_instruments"
    ),
    re_path(
        r"^/instrument_values/?$",
        views.PhenoToolInstrumentValues.as_view(),
        name="pheno_tool_instrument_values"
    ),
]
