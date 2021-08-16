from django.urls import re_path
from . import views

urlpatterns = [
    re_path(r"^/?$", views.GenomicScoresView.as_view(), name="genomic_scores"),
]
