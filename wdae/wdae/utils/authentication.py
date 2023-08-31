"""Module containing a custom OAuth2 authentication class."""

from typing import Optional, Callable
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from rest_framework import exceptions
from oauth2_provider.contrib.rest_framework import OAuth2Authentication


class GPFOAuth2Authentication(OAuth2Authentication):
    """
    Provide custom OAuth2 authentication.

    This authentication class that will return a 401 error in the case that an
    invalid OAuth token has been provided. We need this behaviour as we have
    routes which will allow unauthenticated requests, which in turn prevents
    distinguishing requests with expired tokens from those that bear no
    authentication headers.
    """

    def authenticate(self, request: HttpRequest) -> Optional[tuple]:
        retval = super().authenticate(request)
        if retval is None and request.headers.get("Authorization"):
            raise exceptions.AuthenticationFailed(
                "Invalid or expired OAuth token."
            )
        if retval is not None:
            user, auth = retval
            if user is None:
                # handle federation users, set the user to the app owner
                user = auth.application.user
            return user, auth
        return retval  # no user authenticated, just pass on


def oauth_html_form_patch(
    get_response: Callable[[HttpRequest], HttpResponse]
) -> Callable[[HttpRequest], HttpResponse]:
    """Middleware patch to allow using form-based POST downloads with OAuth."""
    def middleware(request: HttpRequest) -> HttpResponse:
        if request.method == "POST" and \
           request.content_type == "application/x-www-form-urlencoded" and \
           "access_token" in request.POST:
            token = request.POST["access_token"]
            request.META["HTTP_AUTHORIZATION"] = f"Bearer {token}"
        return get_response(request)
    return middleware
