from django.conf.urls import patterns, include, url
from wvdb.views import *
from wvdb.variants import *


urlpatterns = patterns('',
                       url('^hello/$', hello),
                       url('^variants/$', variants_form),
                       url('^results/$', variants_results),                       
)
