"""Django settings for production deployment of gpf-web.

Loaded by both the runtime gunicorn process and the
`collectstatic` step of the web_ui production image build,
so anything imported here MUST be safe to evaluate without a
real GPF instance on disk (no DAE_DB_DIR access, no DB
connection at import time).
"""
# pylint: disable=wildcard-import,unused-wildcard-import
import os

from gpf_instance.feature_flags import DEFAULT_FEATURE_FLAGS

from .default_settings import *  # noqa: F403

DEBUG = False

# Per-flag env-var overrides of web-API feature flags. For every flag in the
# canonical registry, a deployment can flip it by setting
# ``GPF_FEATURE_FLAG__<NAME>`` (name upper-cased). Only ``0``/``false``/``no``
# (case-insensitive) disable; an unset var leaves the flag at its default, so
# adding a flag to DEFAULT_FEATURE_FLAGS makes it deployment-toggleable with no
# further code change. This keeps the mechanism aligned with the stack's
# "all per-host config flows through the container env" convention.
#
# Only flags with a matching env var are emitted here; the rest fall through
# to their registry default when the flags singleton is built. Since
# default_settings leaves FEATURE_FLAGS empty, building this dict fresh is
# equivalent to merging over the inherited value.
_feature_flags: dict[str, bool] = {}
for _flag in DEFAULT_FEATURE_FLAGS:
    _env = f"GPF_FEATURE_FLAG__{_flag.upper()}"
    if _env in os.environ:
        _feature_flags[_flag] = os.environ[_env].lower() not in (
            "0", "false", "no",
        )
FEATURE_FLAGS = _feature_flags

# STATIC_ROOT pinned so the web_ui image's django-static stage
# produces a known path; the Apache stage copies it back out.
STATIC_ROOT = "/static/gpf/static"

# ALLOWED_HOSTS is intentionally permissive in the image; deploy
# wrappers (gain-infra, k8s manifests) override via env if they
# want to lock it down.
ALLOWED_HOSTS = ["*"]

STUDIES_EAGER_LOADING = True
