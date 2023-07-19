"""Module containing a custom OAuth2 authentication class."""

from django.contrib.sessions.models import Session
from users_api.models import WdaeUser
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

    def authenticate(self, request):
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


class GPFOAuth2CookieAuth(GPFOAuth2Authentication):
    """
    Check for a session cookie if no OAuth token is found.

    Used to allow download requests which are made without an OAuth token
    but with a session cookie instead.
    """

    def authenticate(self, request):
        retval = super().authenticate(request)
        if retval is None:
            # As a last resort, check for a session cookie
            try:
                user_id = Session.objects.get(
                    session_key=request.session.session_key
                ).get_decoded().get("_auth_user_id")
                user = WdaeUser.objects.get(id=user_id)
                return user, None
            except (Session.DoesNotExist,    # pylint: disable=no-member
                    WdaeUser.DoesNotExist):  # pylint: disable=no-member
                pass
        return retval
