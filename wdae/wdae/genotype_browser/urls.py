from django.urls import re_path
from genotype_browser import views

urlpatterns = [
    re_path(
        r"^/query/?",
        views.GenotypeBrowserQueryView.as_view(),
        name="genotype_browser_query"
    ),
]
