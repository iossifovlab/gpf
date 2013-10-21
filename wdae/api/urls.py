from django.conf.urls import patterns, url
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = patterns('api.views',
    url(r'^studies/denovo$', 'denovo_studies_list'),
    url(r'^studies/transmitted$', 'transmitted_studies_list'),
)

urlpatterns = format_suffix_patterns(urlpatterns)