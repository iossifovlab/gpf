"""Django settings for production deployment of gpf-web.

Loaded by both the runtime gunicorn process and the
`collectstatic` step of the web_ui production image build,
so anything imported here MUST be safe to evaluate without a
real GPF instance on disk (no DAE_DB_DIR access, no DB
connection at import time).
"""
# pylint: disable=wildcard-import,unused-wildcard-import
from .default_settings import *  # noqa: F401,F403

DEBUG = False

# STATIC_ROOT pinned so the web_ui image's django-static stage
# produces a known path; the Apache stage copies it back out.
STATIC_ROOT = "/static/gpf/static"

# ALLOWED_HOSTS is intentionally permissive in the image; deploy
# wrappers (gain-infra, k8s manifests) override via env if they
# want to lock it down.
ALLOWED_HOSTS = ["*"]

STUDIES_EAGER_LOADING = True
