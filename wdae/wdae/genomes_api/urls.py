from django.conf.urls import url
from . import views

urlpatterns = [
    url(
        r"^/gene_models/default/?$",
        views.DefaultGeneModelsId.as_view(),
        name="default_gene_models",
    ),
    url(
        r"^/gene_models/default/(?P<gene_symbol>.+)$",
        views.GeneModels.as_view(),
        name="gene_models_query",
    ),
]
