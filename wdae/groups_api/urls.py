from rest_framework.routers import SimpleRouter
from groups_api.views import GroupsViewSet


router = SimpleRouter()
router.register(r'', GroupsViewSet, base_name='groups')

urlpatterns = router.urls
