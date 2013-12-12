from django.conf.urls import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = patterns('api.views',
    url(r'^denovo_studies$', 'denovo_studies_list'),
    url(r'^study_groups$', 'study_groups_list'),
    url(r'^transmitted_studies$', 'transmitted_studies_list'),
    url(r'^effect_types$', 'effect_types_list'),
    url(r'^variant_types$', 'variant_types_list'),
    url(r'^families/(?P<study_name>.+)$', 'families_list'),
    # url(r'^gene_set/denovo/(?P<denovo_study>\w+)$', 'gene_set_denovo_list'),
    # url(r'^gene_set/denovo/(?P<denovo_study>\w+)/(?P<gene_set>\w+)$', 'gene_set_denovo_list'),

    # url(r'^gene_set/main$', 'gene_set_main_list'),
    # url(r'^gene_set/main/(?P<gene_set>[\w:\-\+_]+)$', 'gene_set_main_list'),

    # url(r'^gene_set/go$', 'gene_set_go_list'),
    # url(r'^gene_set/go/(?P<gene_set>[\w:\-\+_]+)$', 'gene_set_go_list'),

    # url(r'^gene_set/disease$', 'gene_set_disease_list'),
    # url(r'^gene_set/disease/(?P<gene_set>.+)$', 'gene_set_disease_list'),

    # url(r'^genes$', 'gene_list'),

    url(r'^query_variants_preview$', 'query_variants_preview'),
    url(r'^query_variants$', 'query_variants'),

    url(r'^report_variants$', 'report_variants'),
    url(r'^gene_sets$', 'gene_sets_list'),
    url(r'^gene_set_list$', 'gene_set_list'),
    url(r'^report_studies$', 'report_studies'),
    url(r'^enrichment_test$', 'enrichment_test'),

)

urlpatterns = format_suffix_patterns(urlpatterns)
