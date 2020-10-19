from django.conf.urls import url
from gene_view_api import views

urlpatterns = [
    url(
        r"^/config/?$",
        views.ConfigView.as_view(),
        name="genotype_browser_preview",
    ),
    url(
        r"^/query_summary_variants/?$",
        views.QueryVariantsView.as_view(),
        name="genotype_browser_preview_variants",
    ),
]
