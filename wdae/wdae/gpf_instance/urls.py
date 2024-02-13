from django.urls import re_path
from gpf_instance import views as instance_views


urlpatterns = [
    re_path(
        r"^/version/?$",
        instance_views.version,
        name="version"
    ),
    re_path(
        r"^/description/?$",
        instance_views.DescriptionView.as_view(),
        name="description"
    ),
    re_path(
        r"^/about/?$",
        instance_views.AboutDescriptionView.as_view(),
        name="about"
    )
]
