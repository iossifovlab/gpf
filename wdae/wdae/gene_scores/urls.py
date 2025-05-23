from django.urls import re_path

from gene_scores import views

urlpatterns = [
    re_path(r"^/?$", views.GeneScoresListView.as_view(), name="gene_scores"),
    re_path(
        r"^/histograms/?$",
        views.HistogramView.as_view(),
        name="gene_scores_histograms",
    ),
    re_path(
        r"^/download/(?P<score>.+)$",
        views.GeneScoresDownloadView.as_view(),
        name="gene_scores_download",
    ),
    re_path(
        r"^/partitions/?$",
        views.GeneScoresPartitionsView.as_view(),
        name="gene_scores_partitions",
    ),
]
