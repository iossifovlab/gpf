'''
Created on Nov 16, 2015

@author: lubo
'''
from django.conf.urls import url
from gene_weights import views

urlpatterns = [
    url(r'^$',
        views.GeneWeightsListView.as_view(),
        name="gene_weights"),

]
