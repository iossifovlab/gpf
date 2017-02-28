from rest_framework.authentication import SessionAuthentication 

class DpfSessionAuthentication(SessionAuthentication):
    # def authenticate(self, request):
    #     """
    #     Returns a `User` if the request session currently has a logged in user.
    #     Otherwise returns `None`.
    #     """
    #
    #     # Get the session-based user from the underlying HttpRequest object
    #     user = getattr(request._request, 'user', None)
    #
    #     # Unauthenticated, CSRF validation not required
    #     if not user or not user.is_active:
    #         return None
    #
    #     self.enforce_csrf(request)
    #
    #     # CSRF passed with authenticated user
    #     return (user, None)

    def enforce_csrf(self, request):
        """
        Enforce CSRF validation for session based authentication.
        """
        return
