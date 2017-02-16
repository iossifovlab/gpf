'''
Created on Feb 16, 2017

@author: lubo
'''
from django.conf.urls import url
from gene_sets import views

urlpatterns = [
    url(r'^/collections$',
        views.GeneSetsCollectionsView.as_view(),
        name="gene_sets_collections"),
]
