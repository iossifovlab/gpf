# pylint: disable=W0621,C0114,C0116,W0212,W0613
# flake8: noqa

# pylint: disable=wildcard-import,unused-wildcard-import
from .default_settings import *

# This stops mypy from setting up running a GPF instance when typechecking
# which is slow and unnecessary
INSTALLED_APPS.remove("gpf_instance.apps.WDAEConfig")

# This is here only to prevent false type errors
DEFAULT_WDAE_DIR = None
