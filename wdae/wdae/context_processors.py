from django.conf import settings


def google_oauth(request):
    return {
        "GOOGLE_AUTH_URL": settings.GOOGLE_AUTH_URL,
        "GOOGLE_CLIENT_ID": settings.GOOGLE_CLIENT_ID,
        "GOOGLE_REDIRECT_URI": settings.GOOGLE_REDIRECT_URI,
    }
