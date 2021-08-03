# flake8: noqa
from .default_settings import *

ALLOWED_HOSTS += ["localhost"]

INSTALLED_APPS += [
    "corsheaders",
    "django_extensions",
]


MIDDLEWARE += [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

CORS_ORIGIN_WHITELIST = [
    "http://localhost:8000",
    "http://127.0.0.1:9000",
    "http://localhost:4200",
    "http://127.0.0.1:4200",
]

CORS_ALLOW_CREDENTIALS = True

REMOTES = [
    # {
    #     "id": "REMOTE1",
    #     "host": "localhost",
    #     "base_url": "api/v3",
    #     "port": "8000",
    #     "user": "admin@iossifovlab.com",
    #     "password": "secret",
    # }
]

STUDIES_EAGER_LOADING = False

OPEN_REGISTRATION = True
