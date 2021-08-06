from django.conf.urls import url, include

from gpfjs.views import index

urlpatterns = [
    url(r'^$', index), url(r'^gpfjs/.*$', index),
    url(r"^api/v3/datasets", include("datasets_api.urls")),
    url(r"^api/v3/gene_weights", include("gene_weights.urls")),
    url(r"^api/v3/gene_sets", include("gene_sets.urls")),
    url(r"^api/v3/chromosomes", include("chromosome.urls")),
    url(r"^api/v3/genotype_browser", include("genotype_browser.urls")),
    url(r"^api/v3/enrichment", include("enrichment_api.urls")),
    url(r"^api/v3/", include("users_api.urls")),
    url(r"^api/v3/measures", include("measures_api.urls")),
    url(r"^api/v3/pheno_tool", include("pheno_tool_api.urls")),
    url(r"^api/v3/pheno_browser", include("pheno_browser_api.urls")),
    url(r"^api/v3/common_reports", include("common_reports_api.urls")),
    url(r"^api/v3/genomic_scores", include("genomic_scores_api.urls")),
    url(r"^api/v3/", include("groups_api.urls")),
    url(r"^api/v3/query_state", include("query_state_save.urls")),
    url(r"^api/v3/user_queries", include("user_queries.urls")),
    url(r"^api/v3/genome", include("genomes_api.urls")),
    url(r"^api/v3/gene_view", include("gene_view.urls")),
    url(r"^api/v3/autism_gene_tool", include("autism_gene_profiles_api.urls")),
    url(r"^api/v3/families", include("family_api.urls")),
    url(r"^api/v3/person_sets", include("person_sets_api.urls")),
]
