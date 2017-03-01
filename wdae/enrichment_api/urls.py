'''
Created on Feb 17, 2017

@author: lubo
'''
from django.conf.urls import url
from enrichment_api import views


urlpatterns = [
    url(r'^/models/(?P<dataset_id>.+)/(?P<enrichment_model_type>.+)$',
        views.EnrichmentModelsView.as_view(),
        name="enrichment_models"),

    url(r'^/test$',
        views.EnrichmentTestView.as_view(),
        name="enrichment_test"),

]
