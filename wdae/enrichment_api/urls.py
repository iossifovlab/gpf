'''
Created on Feb 17, 2017

@author: lubo
'''
from __future__ import unicode_literals
from django.conf.urls import url
from enrichment_api import views


urlpatterns = [
    url(r'^/models/(?P<dataset_id>.+)',
        views.EnrichmentModelsView.as_view(),
        name="enrichment_models"),

    url(r'^/test$',
        views.EnrichmentTestView.as_view(),
        name="enrichment_test"),

]
