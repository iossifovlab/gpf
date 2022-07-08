# pylint: disable=W0621,C0114,C0116,W0212,W0613
# flake8: noqa

# pylint: disable=wildcard-import,unused-wildcard-import
from .default_settings import *


INSTALLED_APPS += [
    "corsheaders",
    "gpf_instance.apps.WDAETestingConfig",
]

ALLOWED_HOSTS += [
    "gpfremote",
    "localhost",
]


MIDDLEWARE += [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

CORS_ORIGIN_WHITELIST = [
    "localhost:8000",
    "127.0.0.1:9000",
    "localhost:4200",
    "127.0.0.1:4200",
]

CORS_ALLOW_CREDENTIALS = True


TESTING = True
