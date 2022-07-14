from rest_framework import exceptions
from oauth2_provider.contrib.rest_framework import OAuth2Authentication


class GPFOAuth2Authentication(OAuth2Authentication):
    """
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
        elif retval is not None:
            user, auth = retval
            if user is None:
                # handle federation users, set the user to the app owner
                user = auth.application.user
            return user, auth
        else:
            return retval  # no user authenticated, just pass on
