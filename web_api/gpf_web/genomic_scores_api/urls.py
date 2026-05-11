from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^/?$", views.GenomicScoresView.as_view(), name="genomic_scores"),
    re_path(
        r"^/score_descs/(?P<score_id>.+)?$",
        views.GenomicScoreDescsView.as_view(),
        name="score_desc",
    ),
    re_path(
        r"^/score_descs?$",
        views.GenomicScoreDescsView.as_view(),
        name="score_descs_all",
    ),
]
