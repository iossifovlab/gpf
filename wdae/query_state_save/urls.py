from django.conf.urls import url
from query_state_save.views import QueryStateSaveView, QueryStateLoadView, \
    QueryStateDeleteView

urlpatterns = [
    url(r'^/save', QueryStateSaveView.as_view(), name="save-query"),
    url(r'^/load', QueryStateLoadView.as_view(), name="load-query"),
    url(r'^/delete', QueryStateDeleteView.as_view(), name="delete-query"),
]
