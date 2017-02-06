from django.conf.urls import patterns, url, include


urlpatterns = patterns(
    '',
    url(r'^$', 'variants_angular.views.index'),
    url(r'^api/', include('api.urls')),
    url(r'^api/users/', include('users.urls')),
    url(r'^api/v2/pheno_reports', include('pheno_report.urls')),
    url(r'^api/v2/gene_weights', include('gene_weights.urls')),
    url(r'^api/v2/ssc_pheno_families', include('pheno_families.urls')),
    url(r'^api/v2/ssc_dataset_families', include('ssc_families.urls')),
    url(r'^api/v2/enrichment', include('enrichment.urls')),

    url(r'^api/v3/datasets', include('datasets.urls')),
    url(r'^api/v3/gene_weights', include('gene_weights.urls')),
    url(r'^api/v3/query', include('query.urls')),

)
