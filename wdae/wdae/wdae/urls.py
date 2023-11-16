from django.urls import path, re_path, include
from django.conf import settings

from users_api.views import WdaeLoginView

from gpfjs.views import index, favicon
from gpf_instance.views import version

urlpatterns = [
    re_path(r"^$", index),
    re_path(r"^gpfjs/.*$", index),
    re_path(r"^favicon.ico$", favicon),
    re_path(r"^api/v3/datasets", include("datasets_api.urls")),
    re_path(r"^api/v3/gene_scores", include("gene_scores.urls")),
    re_path(r"^api/v3/gene_sets", include("gene_sets.urls")),
    re_path(r"^api/v3/genotype_browser", include("genotype_browser.urls")),
    re_path(r"^api/v3/enrichment", include("enrichment_api.urls")),
    re_path(r"^api/v3/", include("users_api.urls")),
    re_path(r"^api/v3/measures", include("measures_api.urls")),
    re_path(r"^api/v3/pheno_tool", include("pheno_tool_api.urls")),
    re_path(r"^api/v3/pheno_browser", include("pheno_browser_api.urls")),
    re_path(r"^api/v3/common_reports", include("common_reports_api.urls")),
    re_path(r"^api/v3/genomic_scores", include("genomic_scores_api.urls")),
    re_path(r"^api/v3/", include("groups_api.urls")),
    re_path(r"^api/v3/query_state", include("query_state_save.urls")),
    re_path(r"^api/v3/user_queries", include("user_queries.urls")),
    re_path(r"^api/v3/genome", include("genomes_api.urls")),
    re_path(r"^api/v3/gene_view", include("gene_view.urls")),
    re_path(
        r"^api/v3/autism_gene_tool",
        include("autism_gene_profiles_api.urls")
    ),
    re_path(r"^api/v3/families", include("family_api.urls")),
    re_path(r"^api/v3/person_sets", include("person_sets_api.urls")),
    path("o/", include("oauth2_provider.urls", namespace="oauth2_provider")),
    re_path(r"^accounts/login/?$", WdaeLoginView.as_view(), name="login_user"),
    re_path(r"^api/v3/sentry", include("sentry.urls")),
    re_path(r"^api/v3/version/?$", version),
]

if getattr(settings, "SILKY_PYTHON_PROFILER", False):
    urlpatterns.append(
        path("silk/", include("silk.urls", namespace="silk"))
    )
