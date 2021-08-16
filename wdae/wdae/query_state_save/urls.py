from django.urls import re_path
from .views import QueryStateSaveView, QueryStateLoadView, QueryStateDeleteView

urlpatterns = [
    re_path(r"^/save/?$", QueryStateSaveView.as_view(), name="save-query"),
    re_path(r"^/load/?$", QueryStateLoadView.as_view(), name="load-query"),
    re_path(
        r"^/delete/?$",
        QueryStateDeleteView.as_view(),
        name="delete-query"
    ),
]
