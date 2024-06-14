from django.urls import re_path

from gene_profiles_api import table_views, views

urlpatterns = [
    re_path(
        r"^/table/configuration/?$",
        table_views.TableConfigurationView.as_view(),
        name="gp_table_configuration",
    ),
    re_path(
        r"^/table/rows/?$",
        table_views.TableRowsView.as_view(),
        name="gp_table_rows",
    ),
    re_path(
        r"^/single-view/configuration/?$",
        views.ConfigurationView.as_view(),
        name="gp_single_view_configuration",
    ),
    re_path(
        r"^/single-view/gene/(?P<gene_symbol>.+)/?$",
        views.ProfileView.as_view(),
        name="gp_single_view_profile",
    ),
    re_path(
        r"^/table/gene_symbols/?$",
        table_views.GeneSymbolsView.as_view(),
        name="gp_gene_symbols",
    ),
]
