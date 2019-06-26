'''
Created on Nov 16, 2015

@author: lubo
'''
from __future__ import unicode_literals
from django.conf.urls import url
from pheno_tool_api import views


urlpatterns = [
    url(r'^$', views.PhenoToolView.as_view(), name="pheno_tool"),
    # url(r'^/download$', views.PhenoToolDownload.as_view(),
    #     name="pheno_tool_download"),
]
