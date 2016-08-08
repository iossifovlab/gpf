'''
Created on Jul 6, 2016

@author: lubo
'''
from django.conf.urls import url
from ssc_families.views import SSCFamilyCountersView
import pheno_families


urlpatterns = [
    url(r'^/counter$',
        SSCFamilyCountersView.as_view(),
        name="counter"),
    url(r'^/studies$',
        pheno_families.views.FamilyFilterStudies.as_view(),
        name="family_studies"),

]
