'''
Created on Nov 16, 2015

@author: lubo
'''
from django.conf.urls import url
from families import views

urlpatterns = [
    url(r'^/counter$',
        views.FamilyFilterCountersView.as_view(),
        name="counter"),
    url(r'^/studies$',
        views.FamilyFilterStudies.as_view(),
        name="family_studies"),

]
