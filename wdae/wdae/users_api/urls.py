from django.urls import re_path

from rest_framework.routers import SimpleRouter
from . import views

router = SimpleRouter(trailing_slash=False)
router.register(r"users", views.UserViewSet, basename="users")

urlpatterns = [
    re_path(r"^users/register/?$", views.register),
    re_path(r"^users/login/?$", views.WdaeLoginView.as_view()),
    re_path(r"^users/logout/?$", views.logout),
    re_path(r"^users/get_user_info/?$", views.get_user_info),
    re_path(
        r"^users/forgotten_password/?$",
        views.ForgotPassword.as_view(),
        name="forgotten_password"
    ),
    re_path(
        r"^users/reset_password/?$",
        views.ResetPassword.as_view(),
        name="reset_password"
    ),
    re_path(
        r"^users/set_password/?$",
        views.SetPassword.as_view(),
        name="set_password"
    ),
    re_path(r"^users/change_password/?$", views.change_password),
    re_path(r"^users/check_verif_path/?$", views.check_verif_code),
    re_path(
        r"^users/get_federation_credentials/?$",
        views.get_federation_credentials
    ),
    re_path(
        r"^users/revoke_federation_credentials/?$",
        views.revoke_federation_credentials
    ),
] + router.urls
