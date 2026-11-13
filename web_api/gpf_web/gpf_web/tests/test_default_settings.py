# pylint: disable=W0621,C0114,C0116
import importlib
from collections.abc import Callable, Iterator
from types import ModuleType

import pytest

from gpf_web import default_settings

_TLS_ENV = "WDAE_EMAIL_USE_TLS"


@pytest.fixture
def reload_default_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[Callable[[], ModuleType]]:
    """Reload default_settings on demand, restoring baseline after.

    The settings read the environment only at module import, so a test
    sets the environment and then calls the returned reloader. The
    teardown removes the variable and reloads once more, so no test
    leaves its value on the shared module object.
    """
    def _reload() -> ModuleType:
        return importlib.reload(default_settings)

    yield _reload
    monkeypatch.delenv(_TLS_ENV, raising=False)
    importlib.reload(default_settings)


_FALSE_VALUES = ["", "  ", "False", "false", "0", "no", "'True'"]
_TRUE_VALUES = ["True", "true", "TRUE", "1", "yes", "on", " True "]


def test_email_use_tls_is_false_when_unset(
    monkeypatch: pytest.MonkeyPatch,
    reload_default_settings: Callable[[], ModuleType],
) -> None:
    monkeypatch.delenv(_TLS_ENV, raising=False)

    settings = reload_default_settings()

    assert settings.EMAIL_USE_TLS is False


@pytest.mark.parametrize("value", _FALSE_VALUES)
def test_email_use_tls_is_false_for_value(
    monkeypatch: pytest.MonkeyPatch,
    reload_default_settings: Callable[[], ModuleType],
    value: str,
) -> None:
    monkeypatch.setenv(_TLS_ENV, value)

    settings = reload_default_settings()

    assert settings.EMAIL_USE_TLS is False


@pytest.mark.parametrize("value", _TRUE_VALUES)
def test_email_use_tls_is_true_for_value(
    monkeypatch: pytest.MonkeyPatch,
    reload_default_settings: Callable[[], ModuleType],
    value: str,
) -> None:
    monkeypatch.setenv(_TLS_ENV, value)

    settings = reload_default_settings()

    assert settings.EMAIL_USE_TLS is True


@pytest.mark.parametrize("value", [None, *_FALSE_VALUES, *_TRUE_VALUES])
def test_email_use_tls_is_a_bool(
    monkeypatch: pytest.MonkeyPatch,
    reload_default_settings: Callable[[], ModuleType],
    value: str | None,
) -> None:
    if value is None:
        monkeypatch.delenv(_TLS_ENV, raising=False)
    else:
        monkeypatch.setenv(_TLS_ENV, value)

    settings = reload_default_settings()

    assert isinstance(settings.EMAIL_USE_TLS, bool)
