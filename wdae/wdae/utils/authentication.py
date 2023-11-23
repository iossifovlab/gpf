"""Module containing a custom OAuth2 authentication class."""

from typing import Optional, Callable
from django.http.request import HttpRequest
from django.http.response import HttpResponse

from rest_framework import exceptions
from rest_framework.authentication import SessionAuthentication
from rest_framework.request import Request

from oauth2_provider.contrib.rest_framework import OAuth2Authentication


class SessionAuthenticationWithoutCSRF(SessionAuthentication):

    def enforce_csrf(self, request: Request) -> None:
        """Enforce CSRF validation for session based authentication."""
        return


class SessionAuthenticationWithUnauthenticatedCSRF(SessionAuthentication):
    """Session authentication with unauthenticated CSRF."""

    def authenticate(self, request: Request) -> Optional[tuple]:
        """Return the currently logged-in user or None otherwise."""
        # Get the session-based user from the underlying HttpRequest object
        # pylint: disable=protected-access
        user = getattr(request._request, "user", None)

        self.enforce_csrf(request)

        # CSRF passed with authenticated user
        return (user, None)


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


def oauth_cookie_to_header(
    get_response: Callable[[HttpRequest], HttpResponse]
) -> Callable[[HttpRequest], HttpResponse]:
    """Middleware patch to allow storing OAuth tokens as cookies."""
    def middleware(request: HttpRequest) -> HttpResponse:
        if "access_token" in request.COOKIES:
            token = request.COOKIES["access_token"]
            request.META["HTTP_AUTHORIZATION"] = f"Bearer {token}"
        return get_response(request)
    return middleware
