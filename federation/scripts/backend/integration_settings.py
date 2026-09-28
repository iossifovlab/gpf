"""Django settings for the federation integration-test backend.

Mirrors rest_client's integration_settings (iossifovlab/gpf#1033): the
backend's SQLite DB is throwaway, so it trades crash durability for
fewer fsyncs. WAL with ``synchronous=NORMAL`` commits without an fsync
and never blocks readers, so the healthcheck's reads cannot collide
with a slow commit on an IO-starved agent (iossifovlab/gpf#1035).
"""
# pylint: disable=wildcard-import,unused-wildcard-import
from typing import Any

from gpf_web.settings import *  # ruff: ignore[undefined-local-with-import-star]
from gpf_web.settings import DATABASES

_default: dict[str, Any] = dict(DATABASES["default"])
_default["OPTIONS"] = {
    "init_command": "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;",
}
DATABASES["default"] = _default
