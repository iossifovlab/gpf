'''
Created on Aug 10, 2016

@author: lubo
'''
from __future__ import unicode_literals

from django.conf.urls import url, include

from rest_framework.routers import SimpleRouter
from users_api import views

router = SimpleRouter(trailing_slash=False)
router.register(r'', views.UserViewSet, base_name='users')

urlpatterns = [
    url(r'register$', views.register),
    url(r'login$', views.login),
    url(r'logout$', views.logout),
    url(r'get_user_info$', views.get_user_info),
    url(r'reset_password$', views.reset_password),
    url(r'change_password', views.change_password),
    url(r'check_verif_path', views.check_verif_path),
    url(r'', include(router.urls)),
]
