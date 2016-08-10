'''
Created on Aug 10, 2016

@author: lubo
'''

from django.conf.urls import patterns, url
from rest_framework.authtoken import views as rest_views

urlpatterns = patterns(
    'users.views',
    url(r'^register$', 'register'),
    url(r'^get_user_info$', 'get_user_info'),
    url(r'^check_verif_path', 'check_verif_path'),
    url(r'^change_password', 'change_password'),
    url(r'^reset_password', 'reset_password'),
    url(r'^api-token-auth$', rest_views.obtain_auth_token),

)
