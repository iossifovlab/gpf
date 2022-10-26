# pylint: disable=W0621,C0114,C0116,W0212,W0613
# flake8: noqa

# pylint: disable=wildcard-import,unused-wildcard-import
from .default_settings import *

DEFAULT_OAUTH_APPLICATION_CLIENT = "admin"

ALLOWED_HOSTS += [
    "gpfremote",
    "localhost",
]

CORS_ORIGIN_WHITELIST = [
    "http://localhost:8000",
    "http://127.0.0.1:9000",
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "http://localhost:8001",
]

CORS_ALLOW_CREDENTIALS = True

GPF_INSTANCE_CONFIG = "../../../data/data-hg19-local/gpf_instance.yaml"
