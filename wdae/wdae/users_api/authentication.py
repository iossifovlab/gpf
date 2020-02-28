from rest_framework.authentication import SessionAuthentication


class SessionAuthenticationWithoutCSRF(SessionAuthentication):
    def enforce_csrf(self, request):
        """
        Enforce CSRF validation for session based authentication.
        """
        return


class SessionAuthenticationWithUnauthenticatedCSRF(SessionAuthentication):
    def authenticate(self, request):
        """
        Returns a `User` if the request session currently has a logged in user.
        Otherwise returns `None`.
        """

        # Get the session-based user from the underlying HttpRequest object
        user = getattr(request._request, "user", None)

        self.enforce_csrf(request)

        # CSRF passed with authenticated user
        return (user, None)
