'''
Created on Aug 10, 2016

@author: lubo
'''
from __future__ import unicode_literals

from django.conf.urls import url, include

from rest_framework.routers import SimpleRouter
from users_api import views

router = SimpleRouter(trailing_slash=False)
router.register(r'users', views.UserViewSet, basename='users')

urlpatterns = [
    url(r'users/register$', views.register),
    url(r'users/login$', views.login),
    url(r'users/logout$', views.logout),
    url(r'users/get_user_info$', views.get_user_info),
    url(r'users/reset_password$', views.reset_password),
    url(r'users/change_password', views.change_password),
    url(r'users/check_verif_path', views.check_verif_path),
] + router.urls

