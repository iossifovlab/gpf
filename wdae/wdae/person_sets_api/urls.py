from django.conf.urls import url
from . import views

urlpatterns = [
    url(
        r"^/(?P<dataset_id>.+)/all/?$",
        views.ListAllCollectionsView.as_view(),
        name="list_all_collections",
    ),
    url(
        r"^/(?P<dataset_id>.+)/configs/?$",
        views.CollectionConfigsView.as_view(),
        name="collection_configs",
    ),
    url(
        r"^/(?P<dataset_id>.+)/stats/(?P<collection_id>.+)?$",
        views.CollectionStatsView.as_view(),
        name="collection_stats",
    ),
]
