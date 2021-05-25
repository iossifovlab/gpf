from django.conf.urls import url
from . import views


urlpatterns = [
    url(
        r"^/denied_prompt/?$",
        views.PermissionDeniedPromptView.as_view(),
        name="denied_prompt",
    ),
    url(
        r"^/details/(?P<dataset_id>.+)$",
        views.DatasetDetailsView.as_view(),
        name="dataset_details",
    ),
    url(
        r"^/pedigree/(?P<dataset_id>.+)/(?P<column>.+)$",
        views.DatasetPedigreeView.as_view(),
        name="pedigree",
    ),
    url(
        r"^/config/(?P<dataset_id>.+)$",
        views.DatasetConfigView.as_view(),
        name="dataset_config",
    ),
    url(r"^/(?P<dataset_id>.+)$", views.DatasetView.as_view(), name="dataset"),
    url(r"^/?$", views.DatasetView.as_view(), name="dataset_all"),
]
