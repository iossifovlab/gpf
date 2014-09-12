from django.conf.urls import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = patterns(
    'api.views',
    url(r'^denovo_studies$', 'denovo_studies_list'),
    url(r'^study_groups$', 'study_groups_list'),
    url(r'^transmitted_studies$', 'transmitted_studies_list'),
    url(r'^effect_types$', 'effect_types_list'),
    url(r'^chromes_effect_types$', 'chromes_effect_types'),
    url(r'^variant_types$', 'variant_types_list'),
    url(r'^families/(?P<study_name>.+)$', 'families_list'),

    url(r'^query_variants_preview$', 'query_variants_preview'),
    url(r'^query_variants$', 'query_variants'),

    url(r'^report_variants$', 'report_variants'),
    url(r'^gene_sets$', 'gene_sets_list'),
    url(r'^gene_set_list$', 'gene_set_list'),
    url(r'^report_studies$', 'report_studies'),
    url(r'^enrichment_test$', 'enrichment_test'),
    url(r'^child_types$', 'child_type_list'),
    url(r'^studies_summaries$', 'studies_summaries'),
    

)

urlpatterns = format_suffix_patterns(urlpatterns)
