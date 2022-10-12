# pylint: disable=W0621,C0114,C0116,W0212,W0613
# flake8: noqa

# pylint: disable=wildcard-import,unused-wildcard-import
import os
from .default_settings import *

INSTALLED_APPS += [
    "gpf_instance.apps.WDAEConfig",
]

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

STUDIES_EAGER_LOADING = False

OPEN_REGISTRATION = True

GOOGLE_AUTH_URL = os.environ["GOOGLE_AUTH_URL"]
GOOGLE_TOKEN_URL = os.environ["GOOGLE_TOKEN_URL"]
GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]
GOOGLE_REDIRECT_URI = os.environ["GOOGLE_REDIRECT_URI"]
