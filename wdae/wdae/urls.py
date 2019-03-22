from __future__ import unicode_literals
from django.conf.urls import url, include
from django.contrib import admin

from gpfjs.views import index

admin.autodiscover()
urlpatterns = [
    url(r'^$', index),
    url(r'^gpfjs/.*$', index),
    #     url(r'^api/v2/pheno_reports', include('pheno_report.urls')),
    #     url(r'^api/v2/gene_weights', include('gene_weights.urls')),
    #     url(r'^api/v2/ssc_pheno_families', include('pheno_families.urls')),
    #     url(r'^api/v2/ssc_dataset_families', include('ssc_families.urls')),
    #     url(r'^api/v2/enrichment', include('enrichment.urls')),

    url(r'^api/v3/datasets', include('datasets_api.urls')),
    url(r'^api/v3/gene_weights', include('gene_weights.urls')),
    url(r'^api/v3/gene_sets', include('gene_sets.urls')),
    url(r'^api/v3/chromosomes', include('chromosome.urls')),
    url(r'^api/v3/genotype_browser', include('genotype_browser.urls')),
    # url(r'^api/v3/enrichment', include('enrichment_api.urls')),
    url(r'^api/v3/', include('users_api.urls')),
    url(r'^api/v3/measures', include('measures_api.urls')),
    url(r'^api/v3/family_counters', include('family_counters_api.urls')),
    # url(r'^api/v3/pheno_tool', include('pheno_tool_api.urls')),
    url(r'^api/v3/pheno_browser', include('pheno_browser_api.urls')),
    url(r'^api/v3/common_reports', include('common_reports_api.urls')),
    url(r'^api/v3/genomic_scores', include('genomic_scores_api.urls')),
    url(r'^api/v3/', include('groups_api.urls')),
    url(r'^api/v3/query_state', include('query_state_save.urls')),
    url(r'^admin/', include(admin.site.urls)),
]
