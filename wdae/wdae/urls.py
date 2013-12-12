from django.conf.urls import patterns, url, include


# import api.views
# router = routers.DefaultRouter()
# router.register(r'users', quickstart.views.UserViewSet)
# router.register(r'groups', quickstart.views.GroupViewSet)


# API v1
# router.register(r'studies', api.views.hello_world)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browseable API.
urlpatterns = patterns(
    '',
    url(r'^$', 'variants.views.index'),
    url(r'^api/', include('api.urls')),
)
