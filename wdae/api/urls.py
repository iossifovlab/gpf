from django.conf.urls import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = patterns('api.views',
    url(r'^denovo_studies$', 'denovo_studies_list'),
    url(r'^transmitted_studies$', 'transmitted_studies_list'),
    url(r'^effect_types$', 'effect_types_list'),
    url(r'^variant_types$', 'variant_types_list'),
)

urlpatterns = format_suffix_patterns(urlpatterns)