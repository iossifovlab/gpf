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
        name="pheno_tool_persons",
    ),
    re_path(
        r"^/people_values/?$",
        views.PhenoToolPeopleValues.as_view(),
        name="pheno_tool_people_values",
    ),
    re_path(
        r"^/measure/?$",
        views.PhenoToolMeasure.as_view(),
        name="pheno_tool_measure",
    ),
    re_path(
        r"^/measures/?",
        views.PhenoToolMeasures.as_view(),
        name="pheno_tool_measures",
    ),
    re_path(
        r"^/instruments/?$",
        views.PhenoToolInstruments.as_view(),
        name="pheno_tool_instruments",
    ),
]
