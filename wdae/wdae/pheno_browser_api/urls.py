from django.urls import re_path
from pheno_browser_api import views


urlpatterns = [
    re_path(
        r"^/config/?$",
        views.PhenoConfigView.as_view(),
        name="pheno_browser_config",
    ),
    re_path(
        r"^/instruments/?$",
        views.PhenoInstrumentsView.as_view(),
        name="pheno_browser_instruments",
    ),
    re_path(
        r"^/measures_info/?$",
        views.PhenoMeasuresInfoView.as_view(),
        name="pheno_browser_measures_info",
    ),
    re_path(
        r"^/measures/?$",
        views.PhenoMeasuresView.as_view(),
        name="pheno_browser_measures",
    ),
    re_path(
        r"^/measure_description/?$",
        views.PhenoMeasureDescriptionView.as_view(),
        name="pheno_browser_measure_description",
    ),
    re_path(
        r"^/download/?$",
        views.PhenoMeasuresDownload.as_view(),
        name="pheno_browser_download",
    ),
    re_path(
        r"^/measure_values/?$",
        views.PhenoMeasureValues.as_view(),
        name="pheno_browser_values",
    ),
]
