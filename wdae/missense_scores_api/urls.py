from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$',
        views.MissenseScoresView.as_view(),
        name="missense_scores"),
]
