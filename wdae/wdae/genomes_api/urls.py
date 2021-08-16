from django.urls import re_path
from . import views

urlpatterns = [
    re_path(
        r"^/gene_models/default/?$",
        views.DefaultGeneModelsId.as_view(),
        name="default_gene_models",
    ),
    re_path(
        r"^/gene_models/default/(?P<gene_symbol>.+)$",
        views.GeneModels.as_view(),
        name="gene_models_query",
    ),
    re_path(
        r"^/gene_models/search/(?P<search_term>.+)$",
        views.GeneSymbolsSearch.as_view(),
        name="gene_symbols_search",
    ),
]
