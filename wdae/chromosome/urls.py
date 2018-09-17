from __future__ import unicode_literals
from django.conf.urls import url

from chromosome.views import ChromosomeView


urlpatterns = [
    url(r'^/$',
        ChromosomeView.as_view()),
]
