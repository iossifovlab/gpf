'''
Created on Aug 10, 2016

@author: lubo
'''

from django.conf.urls import patterns, url

urlpatterns = patterns(
    'users_api.views',
    url(r'^register$', 'register'),
    url(r'^login$', 'login'),
    url(r'^logout$', 'logout'),
    url(r'^get_user_info$', 'get_user_info'),
    url(r'^reset_password', 'reset_password'),
    url(r'^change_password', 'change_password'),
    url(r'^check_verif_path', 'check_verif_path'),
)
