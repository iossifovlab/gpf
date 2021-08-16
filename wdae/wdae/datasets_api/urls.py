from django.urls import re_path
from . import views


urlpatterns = [
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
        r"^/(?P<dataset_id>.+)$",
        views.DatasetView.as_view(),
        name="dataset"
    ),
    re_path(r"^/?$", views.DatasetView.as_view(), name="dataset_all"),
]
