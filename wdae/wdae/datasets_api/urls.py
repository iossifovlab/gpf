from django.urls import re_path

from . import views

urlpatterns = [
    re_path(
        r"^/visible/?$",
        views.VisibleDatasetsView.as_view(),
        name="visible",
    ),
    re_path(
        r"^/pedigree/(?P<dataset_id>.+)/(?P<column>[^/]+)/?$",
        views.DatasetPedigreeView.as_view(),
        name="pedigree",
    ),
    re_path(
        r"^/federation/?$",
        views.FederationDatasetsView.as_view(),
        name="datasets_federation",
    ),
    re_path(
        r"^/description/(?P<dataset_id>[^/]+)/?$",
        views.DatasetDescriptionView.as_view(),
        name="dataset_description",
    ),
    re_path(
        r"^/hierarchy/(?P<dataset_id>[^/]+)/?$",
        views.DatasetHierarchyView.as_view(),
        name="dataset_hierarchy",
    ),
    re_path(
        r"^/hierarchy/?$",
        views.DatasetHierarchyView.as_view(),
        name="full_dataset_hierarchy",
    ),
    re_path(
        r"^/permissions/?$",
        views.DatasetPermissionsView.as_view(),
        name="management_details",
    ),
    re_path(
        r"^/permissions/(?P<dataset_id>.+)/?$",
        views.DatasetPermissionsSingleView.as_view(),
        name="management_details",
    ),
    re_path(
        r"^/studies/?$",
        views.DatasetStudiesView.as_view(),
        name="studies",
    ),
    re_path(
        r"^/(?P<dataset_id>[^/]+)/?$",
        views.DatasetView.as_view(),
        name="dataset",
    ),
    re_path(r"^/?$", views.DatasetView.as_view(), name="dataset_all"),
]
