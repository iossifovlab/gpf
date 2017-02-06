'''
Created on Feb 6, 2017

@author: lubo
'''
from django.conf.urls import url
from query import views

urlpatterns = [
    url(r'^/preview$',
        views.QueryPreviewView.as_view(),
        name="dataset_all"),

]
