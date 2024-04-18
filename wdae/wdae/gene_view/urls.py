from django.urls import re_path

from gene_view import views

urlpatterns = [
    re_path(
        r"^/config/?$",
        views.ConfigView.as_view(),
        name="gene_view_config",
    ),
    re_path(
        r"^/query_summary_variants/?$",
        views.QueryVariantsView.as_view(),
        name="gene_view_summary_variants_query",
    ),
    re_path(
        r"^/download_summary_variants/?$",
        views.DownloadSummaryVariantsView.as_view(),
        name="gene_view_summary_variants_download",
    ),
]
