from django.conf.urls import url
from autism_gene_profiles_api import views

urlpatterns = [
    url(
        r"^/configuration/?$",
        views.ConfigurationView.as_view(),
        name="agp_configuration",
    ),
    url(
        r"^/query_summary_variants/?$",
        views.QueryProfilesView.as_view(),
        name="agp_profiles_query",
    ),
    url(
        r"^/download_summary_variants/?$",
        views.ProfileView.as_view(),
        name="agp_profile"
    )
]
