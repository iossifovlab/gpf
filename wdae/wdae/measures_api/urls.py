'''
Created on Mar 30, 2017

@author: lubo
'''

from django.conf.urls import url
from measures_api import views

urlpatterns = [
    url(r'^/type/(?P<measure_type>.+)$',
        views.PhenoMeasuresView.as_view(),
        name="measures_list"),
    url(r'^/partitions$',
        views.PhenoMeasurePartitionsView.as_view(),
        name="measure_partitions"),
    url(r'^/histogram$',
        views.PhenoMeasureHistogramView.as_view(),
        name="measure_histogram"),
    url(r'^/regressions$',
        views.PhenoMeasureRegressionsView.as_view(),
        name="measure_regressions"),
]
