'''
Created on Jul 6, 2016

@author: lubo
'''
from django.conf.urls import url
import families
from ssc_families.views import SSCFamilyCountersView


urlpatterns = [
    url(r'^/counter$',
        SSCFamilyCountersView.as_view(),
        name="counter"),
    url(r'^/studies$',
        families.views.FamilyFilterStudies.as_view(),
        name="family_studies"),

]
