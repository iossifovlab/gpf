# pylint: disable=W0621,C0114,C0116,W0212,W0613
# flake8: noqa

# pylint: disable=wildcard-import,unused-wildcard-import
import os

from .default_settings import *

from dae.pheno.pheno_data import get_pheno_browser_images_dir
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.dae_conf import dae_conf_schema

DEBUG = True

ALLOWED_HOSTS += ["localhost"]

CORS_ORIGIN_WHITELIST = [
    "http://0.0.0.0:8000",
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

GPF_INSTANCE_CONFIG = GPFConfigParser.load_config_dict(
    str(GPF_INSTANCE_CONFIG_PATH), dae_conf_schema,
)

PHENO_BROWSER_CACHE = get_pheno_browser_images_dir(GPF_INSTANCE_CONFIG)

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    ("images", PHENO_BROWSER_CACHE),
)

CORS_ALLOW_CREDENTIALS = True

OPEN_REGISTRATION = False

########################################################

DEFAULT_WDAE_DIR = GPF_INSTANCE_CONFIG_PATH.parent / "wdae"
DEFAULT_WDAE_DIR.mkdir(exist_ok=True)

LOG_DIR = os.environ.get("WDAE_LOG_DIR", str(DEFAULT_WDAE_DIR))

if not os.environ.get("WDAE_DB_HOST"):
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
