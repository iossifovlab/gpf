from django.urls import re_path

from user_queries.views import UserQueryCollectView, UserQuerySaveView

urlpatterns = [
    re_path(r"^/save/?$", UserQuerySaveView.as_view(), name="user-save-query"),
    re_path(
        r"^/collect/?$",
        UserQueryCollectView.as_view(),
        name="user-collect-queries",
    ),
]
