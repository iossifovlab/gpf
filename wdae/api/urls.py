from django.conf.urls import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = patterns('api.views',
    url(r'^denovo_studies$', 'denovo_studies_list'),
    url(r'^study_groups$', 'study_groups_list'),
    url(r'^transmitted_studies$', 'transmitted_studies_list'),
    url(r'^effect_types$', 'effect_types_list'),
    url(r'^variant_types$', 'variant_types_list'),
    url(r'^families/(?P<study_name>.+)$', 'families_list'),
    url(r'^gene_set/denovo/(?P<denovo_study>.+)$', 'gene_set_denovo_list'),
    url(r'^gene_set/main$', 'gene_set_main_list'),
    url(r'^gene_set/go$', 'gene_set_go_list'),
    url(r'^genes$', 'gene_list'),
    url(r'^get_variants_csv$', 'get_variants_csv'),
    
    
)

urlpatterns = format_suffix_patterns(urlpatterns)