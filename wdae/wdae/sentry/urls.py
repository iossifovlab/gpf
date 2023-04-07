from django.urls import re_path

from rest_framework.routers import SimpleRouter
from . import views

router = SimpleRouter(trailing_slash=False)

urlpatterns = [
    re_path(r"^/?$", views.sentry),
]
