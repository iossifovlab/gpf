'''
Created on Nov 16, 2015

@author: lubo
'''
from django.conf.urls import url
from pheno import views

urlpatterns = [
    url(r'^$',
        views.PhenoReportView.as_view(),
        name="pheno_report"),
    url(r'^/download$',
        views.PhenoReportDownloadView.as_view(),
        name="pheno_report_download"),
    url(r'^/measures$',
        views.PhenoMeasuresView.as_view(),
        name="pheno_measures"),
    url(r'^/measure_partitions$',
        views.PhenoMeasurePartitionsView.as_view(),
        name="measure_partitions"),
    url(r'^/measure_histogram$',
        views.PhenoMeasureHistogramView.as_view(),
        name="measure_histogram"),

]
