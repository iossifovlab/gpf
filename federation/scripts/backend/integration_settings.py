"""Django settings for the federation integration-test backend.

Mirrors rest_client's integration_settings (iossifovlab/gpf#1033): the
backend's SQLite DB is throwaway, so it trades crash durability for
fewer fsyncs. WAL with ``synchronous=OFF`` never syncs and never blocks
readers, so the healthcheck's reads cannot collide with a slow sync on
an IO-starved agent (iossifovlab/gpf#1035).

``synchronous=NORMAL`` was not enough: it drops only the sync at commit.
Django closes the connection after each request, and the close of the
last connection checkpoints the WAL and syncs twice under an exclusive
lock. The next write then syncs a new WAL under the write lock. On a
loaded agent such a sync outlasts the 5 s busy timeout
(iossifovlab/gpf#1144).
"""
# pylint: disable=wildcard-import,unused-wildcard-import
from typing import Any

from gpf_web.settings import *  # ruff: ignore[undefined-local-with-import-star]
from gpf_web.settings import DATABASES

_default: dict[str, Any] = dict(DATABASES["default"])
_default["OPTIONS"] = {
    "init_command": "PRAGMA journal_mode=WAL; PRAGMA synchronous=OFF;",
}
DATABASES["default"] = _default
