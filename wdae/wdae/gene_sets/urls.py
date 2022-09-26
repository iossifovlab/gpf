from django.urls import re_path
from gene_sets import views

urlpatterns = [
    re_path(
        r"^/gene_sets_collections/?$",
        views.GeneSetsCollectionsView.as_view(),
        name="gene_sets_collections",
    ),
    re_path(r"^/gene_sets/?$", views.GeneSetsView.as_view(), name="gene_sets"),
    re_path(
        r"^/gene_set_download/?$",
        views.GeneSetDownloadView.as_view(),
        name="gene_set_download",
    ),
    re_path(
        r"^/has_denovo/?$",
        views.GeneSetsHasDenovoView.as_view(),
        name="gene_sets"
    ),
]
