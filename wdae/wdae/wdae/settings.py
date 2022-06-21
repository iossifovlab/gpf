# pylint: disable=W0621,C0114,C0116,W0212,W0613
# flake8: noqa

# pylint: disable=wildcard-import,unused-wildcard-import
from .default_settings import *

ALLOWED_HOSTS += ["localhost"]

INSTALLED_APPS += [
    "corsheaders",
    "oauth2_provider",
    "gpf_instance.apps.WDAEConfig",
]

MIDDLEWARE += [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    'oauth2_provider.middleware.OAuth2TokenMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
    ),
}

CORS_ORIGIN_WHITELIST = [
    "http://localhost:8000",
    "http://127.0.0.1:9000",
    "http://localhost:4200",
    "http://127.0.0.1:4200",
]

OAUTH2_PROVIDER = {
    'OAUTH2_BACKEND_CLASS': 'oauth2_provider.oauth2_backends.JSONOAuthLibCore',
    'REFRESH_TOKEN_EXPIRE_SECONDS': 360000,
    'ACCESS_TOKEN_EXPIRE_SECONDS': 360000,
}

CORS_ALLOW_CREDENTIALS = True

STUDIES_EAGER_LOADING = False

OPEN_REGISTRATION = True
