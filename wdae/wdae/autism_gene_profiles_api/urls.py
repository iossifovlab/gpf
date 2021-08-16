from django.urls import re_path
from autism_gene_profiles_api import views

urlpatterns = [
    re_path(
        r"^/configuration/?$",
        views.ConfigurationView.as_view(),
        name="agp_configuration",
    ),
    re_path(
        r"^/genes/?$",
        views.QueryProfilesView.as_view(),
        name="agp_profiles_query",
    ),
    re_path(
        r"^/genes/(?P<gene_symbol>.+)/?$",
        views.ProfileView.as_view(),
        name="agp_profile"
    )
]
