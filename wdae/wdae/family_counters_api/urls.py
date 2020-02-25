"""
Created on Apr 13, 2017

@author: lubo
"""
from django.conf.urls import url
from family_counters_api import views

urlpatterns = [
    url(
        r"^/counters$", views.FamilyCounters.as_view(), name="family_counters"
    ),
]
