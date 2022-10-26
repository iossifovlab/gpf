# pylint: disable=W0621,C0114,C0116,W0212,W0613
# flake8: noqa

# pylint: disable=wildcard-import,unused-wildcard-import
from .default_settings import *

ALLOWED_HOSTS += ["localhost"]

CORS_ORIGIN_WHITELIST = [
    # For docker-compose
    "http://localhost:9000",
    "http://127.0.0.1:9000",
    # For local development with `ng serve`
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    # For local development
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

CORS_ALLOW_CREDENTIALS = True

OPEN_REGISTRATION = True
