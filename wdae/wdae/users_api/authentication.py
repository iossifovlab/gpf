from rest_framework.authentication import SessionAuthentication


class SessionAuthenticationWithoutCSRF(SessionAuthentication):
    def enforce_csrf(self, request):
        """Enforce CSRF validation for session based authentication."""
        return


class SessionAuthenticationWithUnauthenticatedCSRF(SessionAuthentication):
    """Session authentication with unauthenbticated CSRF."""

    def authenticate(self, request):
        """Return the currently logged-in user or None otherwise."""
        # Get the session-based user from the underlying HttpRequest object
        user = getattr(request._request, "user", None)

        self.enforce_csrf(request)

        # CSRF passed with authenticated user
        return (user, None)
