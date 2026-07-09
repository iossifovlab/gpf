# pylint: disable=W0621,C0114,C0116,W0212,W0613
import importlib
from collections.abc import Callable, Iterator

import pytest
from django.test import override_settings

from gpf_instance.feature_flags import (
    DEFAULT_FEATURE_FLAGS,
    FeatureFlags,
    get_feature_flags,
)
from gpf_web import production_settings


def test_is_enabled_unknown_flag_is_false() -> None:
    flags = FeatureFlags({})
    assert flags.is_enabled("nope") is False


def test_values_are_coerced_to_bool() -> None:
    # Deliberately pass non-bool values to exercise the coercion.
    flags = FeatureFlags(
        {"on": 1, "off": 0, "stringy": "false"},  # type: ignore[dict-item]
    )

    assert flags.is_enabled("on") is True
    assert flags.is_enabled("off") is False
    # A mistyped non-empty string is truthy, but the return is a real bool.
    assert flags.is_enabled("stringy") is True
    assert flags.get_all() == {"on": True, "off": False, "stringy": True}


def test_get_all_returns_a_copy() -> None:
    flags = FeatureFlags({"a": True})
    flags.get_all()["a"] = False
    assert flags.is_enabled("a") is True


@override_settings(FEATURE_FLAGS={})
def test_defaults_used_when_no_override(
    reset_flags: None,  # noqa: ARG001
) -> None:
    assert get_feature_flags().get_all() == DEFAULT_FEATURE_FLAGS


@override_settings(FEATURE_FLAGS={"pheno_browser_download": False})
def test_known_flag_override_applies(
    reset_flags: None,  # noqa: ARG001
) -> None:
    assert get_feature_flags().is_enabled("pheno_browser_download") is False


@override_settings(FEATURE_FLAGS={"made_up_flag": True})
def test_unknown_override_key_is_dropped(
    reset_flags: None,  # noqa: ARG001
) -> None:
    flags = get_feature_flags().get_all()

    assert "made_up_flag" not in flags
    # A stray override key must not disturb the known flags.
    assert flags["pheno_browser_download"] is True


# ---------------------------------------------------------------------------
# production_settings env-var override convention
#
# production_settings derives a FEATURE_FLAGS override from
# ``GPF_FEATURE_FLAG__<NAME>`` env vars (one per known flag). Deployments
# (dory, SFARI) flip a flag off by setting the matching var; pytest runs under
# test_settings, so we exercise the loop by reloading the production_settings
# module directly and inspecting its FEATURE_FLAGS attribute.
# ---------------------------------------------------------------------------
_PHENO_ENV = "GPF_FEATURE_FLAG__PHENO_BROWSER_DOWNLOAD"


@pytest.fixture
def reload_production_settings() -> Iterator[Callable[[], object]]:
    """Reload production_settings on demand, restoring baseline after.

    The env-var loop only runs at module import, so a test toggles env then
    calls the returned reloader. The teardown reloads once more with a clean
    env so no test leaves a toggled FEATURE_FLAGS on the shared module object.
    """
    def _reload() -> object:
        return importlib.reload(production_settings)

    yield _reload
    importlib.reload(production_settings)


def test_env_var_disables_known_flag(
    monkeypatch: pytest.MonkeyPatch,
    reload_production_settings: Callable[[], object],
) -> None:
    monkeypatch.setenv(_PHENO_ENV, "false")
    prod = reload_production_settings()
    assert prod.FEATURE_FLAGS["pheno_browser_download"] is False  # type: ignore[attr-defined]


def test_env_var_enables_known_flag(
    monkeypatch: pytest.MonkeyPatch,
    reload_production_settings: Callable[[], object],
) -> None:
    monkeypatch.setenv(_PHENO_ENV, "true")
    prod = reload_production_settings()
    assert prod.FEATURE_FLAGS["pheno_browser_download"] is True  # type: ignore[attr-defined]


def test_no_env_var_leaves_flag_at_default(
    monkeypatch: pytest.MonkeyPatch,
    reload_production_settings: Callable[[], object],
) -> None:
    monkeypatch.delenv(_PHENO_ENV, raising=False)
    prod = reload_production_settings()
    # No override emitted -> the flag falls through to DEFAULT_FEATURE_FLAGS.
    assert "pheno_browser_download" not in prod.FEATURE_FLAGS  # type: ignore[attr-defined]
