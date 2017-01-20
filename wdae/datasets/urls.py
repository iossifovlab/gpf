'''
Created on Jan 20, 2017

@author: lubo
'''
from django.conf.urls import url
from datasets import views


urlpatterns = [
    url(r'^/dataset$',
        views.DatasetView.as_view(),
        name="dataset_all"),
    url(r'^/dataset/(?P<dataset_id>.+)$',
        views.DatasetView.as_view(),
        name="dataset"),

]
