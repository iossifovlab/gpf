from django.conf.urls import patterns, url, include
from django.contrib import admin

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
    url(r'^$', 'variants.views.index'),
    url(r'^api/', include('api.urls')),
    url(r'^api/', include('variants.urls')),
    url(r'^admin/', include(admin.site.urls) )
)

try:
    from query_prepare import prepare_transmitted_studies, gene_set_bgloader
    from api.enrichment import build_transmitted_background
    from bg_loader import preload_background

    transmitted = prepare_transmitted_studies(
        {"transmittedStudies": 'w873e374s322'})

    builders = [(gene_set_bgloader,
                 ['GO'],
                 'GO'),

                (gene_set_bgloader,
                 ['MSigDB.curated'],
                 'MSigDB.curated'),

                (build_transmitted_background,
                 transmitted,
                 'enrichment_background')
                ]

    preload_background(builders)

except Exception, ex:
    print "Missing import", ex
