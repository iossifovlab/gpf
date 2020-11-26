from django.conf.urls import url
from gene_view import views

urlpatterns = [
    url(
        r"^/config/?$",
        views.ConfigView.as_view(),
        name="gene_view_config",
    ),
    url(
        r"^/query_summary_variants/?$",
        views.QueryVariantsView.as_view(),
        name="gene_view_summary_variants_query",
    ),
    url(
        r"^/download_summary_variants/?$",
        views.DownloadSummaryVariantsView.as_view(),
        name="gene_view_summary_variants_download"
    )
]
