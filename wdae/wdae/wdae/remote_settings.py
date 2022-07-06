# flake8: noqa
from .default_settings import *

ALLOWED_HOSTS += ["localhost"]

INSTALLED_APPS += [
    "django_extensions",
]

CORS_ORIGIN_WHITELIST = [
    "http://localhost:8000",
    "http://127.0.0.1:9000",
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "http://10.0.1.5:4200"
]

CORS_ALLOW_CREDENTIALS = True

STUDIES_EAGER_LOADING = False
