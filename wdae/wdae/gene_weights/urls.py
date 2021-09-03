"""
Created on Nov 16, 2015

@author: lubo
"""
from django.urls import re_path
from gene_weights import views

urlpatterns = [
    re_path(r"^/?$", views.GeneWeightsListView.as_view(), name="gene_weights"),
    re_path(
        r"^/download/(?P<weight>.+)$",
        views.GeneWeightsDownloadView.as_view(),
        name="gene_weights_download",
    ),
    re_path(
        r"^/genes/?$",
        views.GeneWeightsGetGenesView.as_view(),
        name="gene_weights_get_genes",
    ),
    re_path(
        r"^/partitions/?$",
        views.GeneWeightsPartitionsView.as_view(),
        name="gene_weights_partitions",
    ),
]
