from django.conf.urls import patterns, url, include, patterns, url, include
from rest_framework import routers
from rest_framework.routers import DefaultRouter

import quickstart.views
import api

#import api.views
router = routers.DefaultRouter()
router.register(r'users', quickstart.views.UserViewSet)
router.register(r'groups', quickstart.views.GroupViewSet)


# API v1
#router.register(r'studies', api.views.hello_world)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browseable API.
urlpatterns = patterns('',
    url(r'^', include(router.urls)),
    url(r'^api/',include('api.urls')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    
)