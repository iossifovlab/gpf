"""Feature flag registry for the GPF web API."""
from __future__ import annotations

import logging
from threading import Lock
from typing import Any

from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseNotFound

logger = logging.getLogger(__name__)

# Canonical registry of known flags and their default state. A deployment
# overrides individual flags via ``settings.FEATURE_FLAGS``; overrides are
# merged over these defaults, so an override that omits a flag leaves it at
# its default here rather than silently disabling it.
DEFAULT_FEATURE_FLAGS: dict[str, bool] = {
    "pheno_browser_download": True,
}

_FEATURE_FLAGS: FeatureFlags | None = None
_FEATURE_FLAGS_LOCK = Lock()


class FeatureFlags:
    """Singleton registry of web-API feature flags."""

    def __init__(self, flags: dict[str, bool]) -> None:
        self._flags = dict(flags)

    def is_enabled(self, name: str) -> bool:
        """Return True if the named feature is enabled."""
        return self._flags.get(name, False)

    def get_all(self) -> dict[str, bool]:
        """Return all flags as a name→enabled mapping."""
        return dict(self._flags)


class FeatureFlagMixin:
    """Mixin that gates a view behind a feature flag.

    Set ``feature_flag`` on the subclass to the flag name. The view returns
    404 when the flag is disabled so the endpoint is not advertised.

    Usage::

        class MyView(FeatureFlagMixin, QueryBaseView):
            feature_flag = "my_feature"
    """

    feature_flag: str = ""

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any,
    ) -> HttpResponse:
        if self.feature_flag and not get_feature_flags().is_enabled(
                self.feature_flag):
            return HttpResponseNotFound()
        return super().dispatch(  # type: ignore[misc,no-any-return]
            request, *args, **kwargs)


def get_feature_flags() -> FeatureFlags:
    """Return the process-wide FeatureFlags singleton."""
    global _FEATURE_FLAGS  # pylint: disable=global-statement

    if _FEATURE_FLAGS is None:
        with _FEATURE_FLAGS_LOCK:
            if _FEATURE_FLAGS is None:
                overrides: dict[str, bool] = getattr(
                    settings, "FEATURE_FLAGS", {})
                flags = {**DEFAULT_FEATURE_FLAGS, **overrides}
                logger.info("initializing feature flags: %s", flags)
                _FEATURE_FLAGS = FeatureFlags(flags)

    return _FEATURE_FLAGS


def reset_feature_flags() -> None:
    """Drop the cached singleton so the next access re-reads settings.

    Feature flags are snapshotted once per process; call this after changing
    ``settings.FEATURE_FLAGS`` (chiefly in tests via ``override_settings``) so
    the change takes effect.
    """
    global _FEATURE_FLAGS  # pylint: disable=global-statement

    with _FEATURE_FLAGS_LOCK:
        _FEATURE_FLAGS = None
