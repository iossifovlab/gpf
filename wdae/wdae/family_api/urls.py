from django.conf.urls import url
from . import views

urlpatterns = [
    url(
        r"^/(?P<dataset_id>.+)/(?P<family_id>.+)/members/(?P<member_id>.+)/?$",
        views.MemberDetailsView.as_view(),
        name="member_details",
    ),
    url(
        r"^/(?P<dataset_id>.+)/(?P<family_id>.+)/members/?$",
        views.ListMembersView.as_view(),
        name="list_members",
    ),
    url(
        r"^/(?P<dataset_id>.+)/(?P<family_id>.+)/?$",
        views.FamilyDetailsView.as_view(),
        name="family_details",
    ),
    url(
        r"^/(?P<dataset_id>.+)/?$",
        views.ListFamiliesView.as_view(),
        name="list_families",
    ),
]
