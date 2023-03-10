"""Default Django settings for wdae project."""
# flake8: noqa: F501

import os
import logging
from dae.pheno.pheno_db import get_pheno_browser_images_dir

DEBUG = True


STUDIES_EAGER_LOADING = False

OPEN_REGISTRATION = True

DISABLE_PERMISSIONS = False

SITE_URL = "localhost"

BASE_DIR = os.path.dirname(__file__)

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",  # default
)

MANAGERS = ADMINS

RESET_PASSWORD_TIMEOUT_HOURS = 24

DEFAULT_OAUTH_APPLICATION_CLIENT = "gpfjs"

EMAIL_VERIFICATION_HOST = "http://localhost:8000"
EMAIL_VERIFICATION_SET_PATH = "/api/v3/users/set_password?code={}"
EMAIL_VERIFICATION_RESET_PATH = "/api/v3/users/reset_password?code={}"

EMAIL_HOST = os.environ.get("WDAE_EMAIL_HOST", "localhost")
EMAIL_USET_TLS = os.environ.get("WDAE_EMAIL_USET_TLS", False)
EMAIL_HOST_USER = os.environ.get("WDAE_EMAIL_HOST_USER", None)
EMAIL_HOST_PASSWORD = os.environ.get("WDAE_EMAIL_HOST_PASSWORD", None)

EMAIL_PORT = os.environ.get("WDAE_EMAIL_PORT", 1025)
if EMAIL_PORT is not None:
    EMAIL_PORT = int(EMAIL_PORT)

EMAIL_SUBJECT_PREFIX = "[GPF] "

DEFAULT_FROM_EMAIL = os.environ.get(
    "WDAE_DEFAULT_FROM_EMAIL", "no-reply@iossifovlab.com")

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"


# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["*"]

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = "America/Chicago"

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = "en-us"

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# # If you set this to False, Django will not format dates, numbers and
# # calendars according to the current locale.
# USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ""

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ""

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = ""

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = "static/"

APPEND_SLASH = False


PHENO_BROWSER_CACHE = get_pheno_browser_images_dir()

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    ("images", PHENO_BROWSER_CACHE),
)


# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = os.environ.get(
    "SECRET_KEY", "#mhbhbjgub==v$cjdu7jay@*$ux$novw#t2tmgjr^5(pr@ycxp"
)


MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    # Uncomment the next line for simple clickjacking protection:
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "oauth2_provider.middleware.OAuth2TokenMiddleware",
]

ROOT_URLCONF = "wdae.urls"

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = "wdae.wsgi.application"

PROJECT_ROOT = os.path.abspath(
    os.path.dirname(os.path.dirname(__file__)))

INSTALLED_APPS = [
    # BEGINNING OF THIRD-PARTY APPS

    "django.contrib.admin",
    "django.contrib.messages",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "django.contrib.sessions",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",

    # END OF THIRD-PARTY APPS


    # BEGINNING OF FIRST-PARTY APPS (almost)

    # the gpfjs application contains static files and a simple view
    # that handles missing compiled gpfjs files with a friendly error message
    # (please do not move it)
    "gpfjs",
    "utils",
    "gene_scores",
    "gene_sets",
    "datasets_api",
    "genotype_browser",
    "enrichment_api",
    "measures_api",
    "pheno_browser_api",
    "common_reports_api",
    "pheno_tool_api",
    "users_api",
    # oauth2_provider is a THIRD-PARTY APP, but must be placed AFTER users_api
    # so that users_api app can override templates from oauth2_provider app
    "oauth2_provider",
    "groups_api",
    "query_state_save",
    "user_queries",
    "gpf_instance.apps.WDAEConfig",

    # END OF FIRST-PARTY APPS
]

AUTH_USER_MODEL = "users_api.WdaeUser"

REST_FRAMEWORK = {
    "PAGINATE_BY": 10,
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "utils.authentication.GPFOAuth2Authentication",
    ),
    "DEFAULT_PAGINATION_CLASS": (
        "utils.pagination.WdaePageNumberPagination"
    ),
    "PAGE_SIZE": 25
}

OAUTH2_PROVIDER = {
    "OAUTH2_BACKEND_CLASS": "oauth2_provider.oauth2_backends.JSONOAuthLibCore",
    "REFRESH_TOKEN_EXPIRE_SECONDS": 18000,
    "ACCESS_TOKEN_EXPIRE_SECONDS": 36000,
}

SESSION_SERIALIZER = "django.contrib.sessions.serializers.JSONSerializer"

# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True


class CustomFormatter(logging.Formatter):
    """A custom formatter that uses color for console output."""

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    fmt_normal = "%(levelname)s %(asctime)s [%(module)s] %(message)s"
    # fmt_invert highlights the `levelname` variable by swapping
    # the background and foreground colors
    fmt_invert = "\x1b[7m%(levelname)s\x1b[27m %(asctime)s [%(module)s] %(message)s"
    time_fmt = "%H:%M:%S"

    FORMATS = {
        logging.DEBUG: logging.Formatter(grey + fmt_normal + reset, time_fmt),
        logging.INFO: logging.Formatter(grey + fmt_normal + reset, time_fmt),
        logging.WARNING: logging.Formatter(yellow + fmt_invert + reset, time_fmt),
        logging.ERROR: logging.Formatter(red + fmt_invert + reset, time_fmt),
        logging.CRITICAL: logging.Formatter(bold_red + fmt_invert + reset, time_fmt),
    }

    def format(self, record):
        formatter = self.FORMATS.get(record.levelno)
        return formatter.format(record)


CONSOLE_LOGGING_LEVEL = "INFO"


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}
    },
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d "
            "%(thread)d %(message)s"
        },
        "verbose_console": {"()": CustomFormatter},
    },
    "handlers": {
        "console": {
            "level": CONSOLE_LOGGING_LEVEL,
            "class": "logging.StreamHandler",
            "formatter": "verbose_console",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["logfile", "logdebug"],
            "propagate": True,
            "level": "INFO",
        },
        "wdae.api": {
            "handlers": ["logfile"],
            "level": "DEBUG",
            "propagate": True,
        },
        "impala": {
            "handlers": ["console", "logdebug"],
            "level": "WARNING",
            "propagate": True,
        },
        "fsspec": {
            "handlers": ["console", "logdebug"],
            "level": "WARNING",
            "propagate": True,
        },
        "matplotlib": {
            "handlers": ["console", "logdebug"],
            "level": "INFO",
            "propagate": True,
        },
        "": {
            "handlers": ["console", "logdebug"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}


# CACHES = {
#     "default": {
#         "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
#         "LOCATION": os.path.join(
#             os.environ.get("DAE_DB_DIR", ""),
#             "wdae/wdae_django_default.cache"),
#         "TIMEOUT": 3600,
#         "OPTIONS": {"MAX_ENTRIES": 10000},
#     },
#     "long": {
#         "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
#         "LOCATION": os.path.join(
#             os.environ.get("DAE_DB_DIR", ""),
#             "wdae/wdae_django_default.cache"),
#         "TIMEOUT": 86400,
#         "OPTIONS": {"MAX_ENTRIES": 1000, },
#     },
#     "pre": {
#         "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
#         "LOCATION": os.path.join(
#             os.environ.get("DAE_DB_DIR", ""), "wdae/wdae_django_pre.cache"),
#         "TIMEOUT": None,
#     },
#     "enrichment": {
#         "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
#         "LOCATION": "unique-snowflake",
#         "TIMEOUT": 60,
#     },
#     # 'default': {
#     #     'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
#     #     'LOCATION': '127.0.0.1:11211',
#     #     'TIMEOUT': 3600,
#     #     'OPTIONS': {
#     #         'MAX_ENTRIES': 10000
#     #     }
#     # },
#     # 'long': {
#     #     'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
#     #     'LOCATION': '127.0.0.1:11211',
#     #     'TIMEOUT': 2592000,
#     #     'OPTIONS': {
#     #         'MAX_ENTRIES': 1000
#     #     }
#     # },
# }

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "debug": DEBUG,
        },
    },
]

# try:
#     from local_settings import *  # @UnusedWildImport
# except ImportError as e:
#     if "local_settings" not in str(e):
#         raise e
