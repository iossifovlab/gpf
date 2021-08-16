"""
Created on Aug 10, 2016
@author: lubo
"""
from django.urls import re_path

from rest_framework.routers import SimpleRouter
from . import views

router = SimpleRouter(trailing_slash=False)
router.register(r"users", views.UserViewSet, basename="users")

urlpatterns = [
    re_path(r"^users/register/?$", views.register),
    re_path(r"^users/login/?$", views.login),
    re_path(r"^users/logout/?$", views.logout),
    re_path(r"^users/get_user_info/?$", views.get_user_info),
    re_path(r"^users/reset_password/?$", views.reset_password),
    re_path(r"^users/change_password/?$", views.change_password),
    re_path(r"^users/check_verif_path/?$", views.check_verif_path),
] + router.urls
