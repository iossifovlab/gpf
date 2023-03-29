# pylint: disable=W0621,C0114,C0116,W0212,W0613
# flake8: noqa

# pylint: disable=wildcard-import,unused-wildcard-import
import os

from gpf_instance.gpf_instance import get_wgpf_instance_path

from .default_settings import *

DEBUG = True
LOGGING_CONFIG = None


ALLOWED_HOSTS += ["localhost"]

CORS_ORIGIN_WHITELIST = [
    "http://0.0.0.0:8000",
]

CORS_ALLOW_CREDENTIALS = True

OPEN_REGISTRATION = True

########################################################

DEFAULT_WDAE_DIR = os.path.join(
    get_wgpf_instance_path(), "wdae")
os.makedirs(DEFAULT_WDAE_DIR, exist_ok=True)

LOG_DIR = os.environ.get("WDAE_LOG_DIR", DEFAULT_WDAE_DIR)

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
        "logdebug": {
            "level": "DEBUG",
            "class": "logging.handlers.WatchedFileHandler",
            "filename": os.path.join(
                LOG_DIR, "wdae-debug.log"),
            "formatter": "verbose",
        },
})
