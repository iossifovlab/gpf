# pylint: disable=W0621,C0114,C0116,W0212,W0613
from django.test import override_settings

from gpf_instance.feature_flags import (
    DEFAULT_FEATURE_FLAGS,
    FeatureFlags,
    get_feature_flags,
)


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
