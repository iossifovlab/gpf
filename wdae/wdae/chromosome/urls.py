from django.urls import re_path

from chromosome.views import ChromosomeView


urlpatterns = [
    re_path(r"^/?$", ChromosomeView.as_view()),
]
