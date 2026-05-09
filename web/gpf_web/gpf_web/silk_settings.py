# pylint: disable=W0621,C0114,C0116,W0212,W0613
# flake8: noqa

# pylint: disable=wildcard-import,unused-wildcard-import
import os

from .settings import *

DEBUG = True

MIDDLEWARE.insert(0, "silk.middleware.SilkyMiddleware")
INSTALLED_APPS.insert(INSTALLED_APPS.index("gpfjs"), "silk")

SILKY_PYTHON_PROFILER = True
SILKY_PYTHON_PROFILER_BINARY = True
SILKY_PYTHON_PROFILER_EXTENDED_FILE_NAME = True

SILKY_PYTHON_PROFILER_RESULT_PATH = os.path.join(DEFAULT_WDAE_DIR, "profiling")
os.makedirs(SILKY_PYTHON_PROFILER_RESULT_PATH, exist_ok=True)

STATIC_ROOT = os.path.join(DEFAULT_WDAE_DIR, "static")
os.makedirs(STATIC_ROOT, exist_ok=True)
