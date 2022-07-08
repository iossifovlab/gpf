"""Default Django settings for wdae project."""

import os
from dae.pheno.pheno_db import get_pheno_browser_images_dir

DEBUG = True


STUDIES_EAGER_LOADING = False

OPEN_REGISTRATION = True

SITE_URL = "localhost"

BASE_DIR = os.path.dirname(__file__)

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",  # default
)

MANAGERS = ADMINS

EMAIL_VERIFICATION_HOST = "http://localhost:8000"
EMAIL_VERIFICATION_PATH = "/gpfjs/validate/{}"


""" Set these for production"""
# EMAIL_USE_TLS = True
# EMAIL_HOST =
# EMAIL_PORT =
# EMAIL_HOST_USER
# EMAIL_HOST_PASSWORD

DEFAULT_FROM_EMAIL = "no-reply@iossifovlab.com"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DEFAULT_WDAE_DIR = os.path.join(
    os.environ.get("DAE_DB_DIR", ""), "wdae")
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
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
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
]

ROOT_URLCONF = "wdae.urls"

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = "wdae.wsgi.application"

PROJECT_ROOT = os.path.abspath(
    os.path.dirname(os.path.dirname(__file__)))

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.messages",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "django.contrib.sessions",
    "rest_framework",
    "rest_framework.authtoken",
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
    "groups_api",
    "gpfjs",
    "query_state_save",
    "user_queries",
    "gpf_instance.apps.WDAEConfig",
]

AUTH_USER_MODEL = "users_api.WdaeUser"

REST_FRAMEWORK = {
    "PAGINATE_BY": 10,
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "users_api.authentication.SessionAuthenticationWithoutCSRF",
    ),
    # 'DEFAULT_RENDERER_CLASSES': (
    #     'rest_framework.renderers.JSONRenderer',
    # )
}

SESSION_SERIALIZER = "django.contrib.sessions.serializers.JSONSerializer"

# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True


# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
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
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
        # Log to a text file that can be rotated by logrotate
        "logfile": {
            "class": "logging.handlers.WatchedFileHandler",
            "filename": os.path.join(
                DEFAULT_WDAE_DIR, "wdae-api.log"),
            "filters": ["require_debug_false"],
            "formatter": "verbose",
        },
        "logdebug": {
            "class": "logging.handlers.WatchedFileHandler",
            "filename": os.path.join(
                DEFAULT_WDAE_DIR, "wdae-debug.log"),
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["logfile", "logdebug"],
            "propagate": True,
            "level": "INFO",
        },
        # 'django.request': {
        #     'handlers': ['console'],
        #     'level': 'WARN',
        #     'propagate': True,
        # },
        "wdae.api": {
            "handlers": ["logfile"],
            "level": "DEBUG",
            "propagate": True,
        },
        "impala": {
            "handlers": ["console", "logdebug"],  # 'logfile'],
            "level": "WARNING",
            "propagate": True,
        },
        "fsspec": {
            "handlers": ["console", "logdebug"],  # 'logfile'],
            "level": "WARNING",
            "propagate": True,
        },
        "matplotlib": {
            "handlers": ["console", "logdebug"],  # 'logfile'],
            "level": "INFO",
            "propagate": True,
        },
        "": {
            "handlers": ["console", "logdebug"],  # 'logfile'],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": os.path.join(
            os.environ.get("DAE_DB_DIR", ""),
            "wdae/wdae_django_default.cache"),
        "TIMEOUT": 3600,
        "OPTIONS": {"MAX_ENTRIES": 10000},
    },
    "long": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": os.path.join(
            os.environ.get("DAE_DB_DIR", ""),
            "wdae/wdae_django_default.cache"),
        "TIMEOUT": 86400,
        "OPTIONS": {"MAX_ENTRIES": 1000, },
    },
    "pre": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": os.path.join(
            os.environ.get("DAE_DB_DIR", ""), "wdae/wdae_django_pre.cache"),
        "TIMEOUT": None,
    },
    "enrichment": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
        "TIMEOUT": 60,
    },
    # 'default': {
    #     'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
    #     'LOCATION': '127.0.0.1:11211',
    #     'TIMEOUT': 3600,
    #     'OPTIONS': {
    #         'MAX_ENTRIES': 10000
    #     }
    # },
    # 'long': {
    #     'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
    #     'LOCATION': '127.0.0.1:11211',
    #     'TIMEOUT': 2592000,
    #     'OPTIONS': {
    #         'MAX_ENTRIES': 1000
    #     }
    # },
}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.normpath(
                os.path.join(PROJECT_ROOT, "gpfjs", "static", "gpfjs")
            ),
            os.path.normpath(
                os.path.join(PROJECT_ROOT, "gpfjs", "static", "empty")
            ),
        ],
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
