from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$',
        views.GenomicScoresView.as_view(),
        name="genomic_scores"),
]
