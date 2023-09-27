from django.urls import re_path
from . import views


urlpatterns = [
    re_path(
        r"^/visible/?$",
        views.VisibleDatasetsView.as_view(),
        name="visible",
    ),
    re_path(
        r"^/denied_prompt/?$",
        views.PermissionDeniedPromptView.as_view(),
        name="denied_prompt",
    ),
    re_path(
        r"^/details/(?P<dataset_id>.+)$",
        views.DatasetDetailsView.as_view(),
        name="dataset_details",
    ),
    re_path(
        r"^/pedigree/(?P<dataset_id>.+)/(?P<column>.+)$",
        views.DatasetPedigreeView.as_view(),
        name="pedigree",
    ),
    re_path(
        r"^/config/(?P<dataset_id>.+)$",
        views.DatasetConfigView.as_view(),
        name="dataset_config",
    ),
    re_path(
        r"^/description/(?P<dataset_id>.+)$",
        views.DatasetDescriptionView.as_view(),
        name="dataset_description"
    ),
    re_path(
        r"^/hierarchy/?$",
        views.DatasetHierarchyView.as_view(),
        name="dataset_hierarchy"
    ),
    re_path(
        r"^/permissions/?$",
        views.DatasetPermissionsView.as_view(),
        name="management_details"
    ),
    re_path(
        r"^/permissions/(?P<dataset_id>.+)/?$",
        views.DatasetPermissionsSingleView.as_view(),
        name="management_details"
    ),
    re_path(
        r"^/studies/?$",
        views.StudiesView.as_view(),
        name="list_studies"
    ),
    re_path(
        r"^/(?P<dataset_id>.+)$",
        views.DatasetView.as_view(),
        name="dataset"
    ),
    re_path(r"^/?$", views.DatasetView.as_view(), name="dataset_all"),
]
