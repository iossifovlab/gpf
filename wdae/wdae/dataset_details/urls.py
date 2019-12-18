from django.conf.urls import url
from dataset_details.views import DatasetDetailsView

urlpatterns = [
    url(r'/(?P<dataset_id>.+)$', DatasetDetailsView.as_view())
]
