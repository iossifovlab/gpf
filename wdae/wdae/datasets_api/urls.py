'''
Created on Jan 20, 2017

@author: lubo
'''
from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^$',
        views.DatasetView.as_view(),
        name="dataset_all"),
    url(r'^/(?P<dataset_id>.+)$',
        views.DatasetView.as_view(),
        name="dataset"),
]
