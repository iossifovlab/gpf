'''
Created on Jul 14, 2016

@author: lubo
'''
from django.conf.urls import url

from enrichment import views

urlpatterns = [
    url(r'^/models/(?P<enrichment_model_type>.+)$',
        views.EnrichmentModelsView.as_view(),
        name="enrichment_models"),

    url(r'^/test$',
        views.EnrichmentView.as_view(),
        name="enrichment_test"),
]
