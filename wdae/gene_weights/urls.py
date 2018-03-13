'''
Created on Nov 16, 2015

@author: lubo
'''
from django.conf.urls import url
from gene_weights import views

urlpatterns = [
    url(r'^$',
        views.GeneWeightsListView.as_view(),
        name="gene_weights"),
    url(r'^/download/(?P<weight>.+)$',
        views.GeneWeightsDownloadView.as_view(),
        name="gene_weights_download"),
    url(r'^/genes$',
        views.GeneWeightsGetGenesView.as_view(),
        name="gene_weights_get_genes"),
    url(r'^/partitions$',
        views.GeneWeightsPartitionsView.as_view(),
        name="gene_weights_partitions")
]
