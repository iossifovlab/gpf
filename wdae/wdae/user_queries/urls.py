from django.conf.urls import url
from user_queries.views import UserQuerySaveView, UserQueryCollectView

urlpatterns = [
    url(r"^/save", UserQuerySaveView.as_view(), name="user-save-query"),
    url(
        r"^/collect",
        UserQueryCollectView.as_view(),
        name="user-collect-queries",
    ),
]
