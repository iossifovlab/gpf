from django.urls import re_path
from . import views

urlpatterns = [
    re_path(
        r"^/(?P<dataset_id>.+)/configs/?$",
        views.CollectionConfigsView.as_view(),
        name="collection_configs",
    ),
    re_path(
        r"^/(?P<dataset_id>.+)/domain/?$",
        views.CollectionDomainView.as_view(),
        name="collection_configs",
    ),
    re_path(
        r"^/(?P<dataset_id>.+)/stats/(?P<collection_id>.+)?$",
        views.CollectionStatsView.as_view(),
        name="collection_stats",
    ),
]
