# pylint: disable=W0621,C0114,C0116,W0212,W0613
# flake8: noqa

# pylint: disable=wildcard-import,unused-wildcard-import
from .default_settings import *

INSTALLED_APPS += [
    "gpf_instance.apps.WDAEConfig",
]

ALLOWED_HOSTS += ["localhost"]

CORS_ORIGIN_WHITELIST = [
    "http://localhost:8000",
    "http://127.0.0.1:9000",
    "http://localhost:4200",
    "http://127.0.0.1:4200",
]

CORS_ALLOW_CREDENTIALS = True

STUDIES_EAGER_LOADING = False

OPEN_REGISTRATION = True
