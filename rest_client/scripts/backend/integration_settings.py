"""Django settings for the rest_client integration-test backend.

The backend's SQLite DB is throwaway, so it trades crash durability for
fewer fsyncs: WAL with ``synchronous=NORMAL`` commits without an fsync
and never blocks readers. On an IO-starved agent the default rollback
journal made a single write request outlast the client's 10 s read
timeout, and the healthcheck's reads hit ``database is locked``
(iossifovlab/gpf#1033).
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
