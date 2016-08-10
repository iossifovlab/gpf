from django.conf.urls import patterns, url, include
from django.contrib import admin
# from denovo_gene_sets import build_denovo_gene_sets

# import api.views
# router = routers.DefaultRouter()
# router.register(r'users', quickstart.views.UserViewSet)
# router.register(r'groups', quickstart.views.GroupViewSet)


# API v1
# router.register(r'studies', api.views.hello_world)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browseable API.


admin.autodiscover()
urlpatterns = patterns(
    '',
    url(r'^$', 'variants_angular.views.index'),
    url(r'^api/', include('api.urls')),
    url(r'^api/users/', include('users.urls')),
    url(r'^angular/', 'variants_angular.views.index'),
)
