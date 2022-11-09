# pylint: disable=W0621,C0114,C0116,W0212,W0613
# flake8: noqa

# pylint: disable=wildcard-import,unused-wildcard-import
import os
import tempfile

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

OPEN_REGISTRATION = True

########################################################

GPF_INSTANCE_CONFIG = "../../../data/data-hg19-local/gpf_instance.yaml"

DEFAULT_WDAE_DIR = tempfile.mkdtemp(prefix="wdae")
os.makedirs(DEFAULT_WDAE_DIR, exist_ok=True)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(
            DEFAULT_WDAE_DIR, "wdae.sql"),
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
    }
}


LOGGING["handlers"].update({  # type: ignore
        # Log to a text file that can be rotated by logrotate
        "logfile": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "logdebug": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
})
