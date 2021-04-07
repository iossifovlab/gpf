"""
Created on Feb 16, 2017

@author: lubo
"""
from django.conf.urls import url
from gene_sets import views

urlpatterns = [
    url(
        r"^/gene_sets_collections/?$",
        views.GeneSetsCollectionsView.as_view(),
        name="gene_sets_collections",
    ),
    url(r"^/gene_sets/?$", views.GeneSetsView.as_view(), name="gene_sets"),
    url(
        r"^/gene_set_download/?$",
        views.GeneSetDownloadView.as_view(),
        name="gene_set_download",
    ),
    url(
        r"^/has_denovo/?$",
        views.GeneSetsHasDenovoView.as_view(),
        name="gene_sets"
    ),
]
