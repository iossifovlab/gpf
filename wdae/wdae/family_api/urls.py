from django.urls import re_path
from . import views

urlpatterns = [
    re_path(
        r"^/tags/?$",
        views.TagsView.as_view(),
        name="list_tags",
    ),
    re_path(
        r"^/(?P<dataset_id>[^/]+)/all/?$",
        views.ListAllDetailsView.as_view(),
        name="list_all_details",
    ),
    re_path(
        r"^/(?P<dataset_id>[^/]+)/(?P<family_id>[^/]+)/members/all/?$",
        views.AllMemberDetailsView.as_view(),
        name="all_member_details",
    ),
    re_path(
        r"^/(?P<dataset_id>[^/]+)/(?P<family_id>[^/]+)"
        r"/members/(?P<member_id>[^/]+)/?$",
        views.MemberDetailsView.as_view(),
        name="member_details",
    ),
    re_path(
        r"^/(?P<dataset_id>[^/]+)/(?P<family_id>[^/]+)/members/?$",
        views.ListMembersView.as_view(),
        name="list_members",
    ),
    re_path(
        r"^/(?P<dataset_id>[^/]+)/(?P<family_id>[^/]+)/?$",
        views.FamilyDetailsView.as_view(),
        name="family_details",
    ),
    re_path(
        r"^/(?P<dataset_id>[^/]+)/?$",
        views.ListFamiliesView.as_view(),
        name="list_families",
    ),
]
