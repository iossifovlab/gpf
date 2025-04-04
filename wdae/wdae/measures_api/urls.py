from django.urls import re_path

from measures_api import views

urlpatterns = [
    re_path(
        r"^/type/(?P<measure_type>.+)$",
        views.PhenoMeasuresView.as_view(),
        name="measures_list",
    ),
    re_path(
        r"^/list/?$",
        views.PhenoMeasureListView.as_view(),
        name="measure_ids_list",
    ),
    re_path(
        r"^/partitions/?$",
        views.PhenoMeasurePartitionsView.as_view(),
        name="measure_partitions",
    ),
    re_path(
        r"^/histogram/?$",
        views.PhenoMeasureHistogramView.as_view(),
        name="measure_histogram",
    ),
    re_path(
        r"^/histogram-beta/?$",
        views.PhenoMeasureHistogramViewBeta.as_view(),
        name="measure_histogram_beta",
    ),
    re_path(
        r"^/role-list/?$",
        views.PhenoDataRoleListView.as_view(),
        name="measure_histogram",
    ),
    re_path(
        r"^/regressions/?$",
        views.PhenoMeasureRegressionsView.as_view(),
        name="measure_regressions",
    ),
]
