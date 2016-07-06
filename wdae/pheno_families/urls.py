'''
Created on Jul 6, 2016

@author: lubo
'''
from django.conf.urls import url
import families
import pheno_families


urlpatterns = [
    url(r'^/counter$',
        pheno_families.views.PhenoFamilyCountersView.as_view(),
        name="counter"),
    url(r'^/studies$',
        families.views.FamilyFilterStudies.as_view(),
        name="family_studies"),

]
