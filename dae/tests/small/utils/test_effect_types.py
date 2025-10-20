# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from dae.effect_annotation.effect import EffectTypesMixin


@pytest.fixture(scope="session")
def query_base() -> EffectTypesMixin:
    return EffectTypesMixin()


def test_build_effect_types(
    query_base: EffectTypesMixin,
) -> None:
    effect_types = "Frame-shift,Nonsense,Splice-site,Non coding"

    res = query_base.build_effect_types(effect_types)
    assert res is not None
    assert res == ["frame-shift", "nonsense", "splice-site", "non-coding"]


def test_build_effect_types_lgds(
    query_base: EffectTypesMixin,
) -> None:
    effect_types = "LGDs"

    res = query_base.build_effect_types(effect_types)
    assert res is not None
    assert {
        "frame-shift",
        "nonsense",
        "splice-site",
        "no-frame-shift-newStop",
    } == set(res)


def test_build_effect_types_mixed(
    query_base: EffectTypesMixin,
) -> None:
    effect_types = "LGDs,CNV, noStart"

    res = query_base.build_effect_types(effect_types)
    assert res is not None
    assert {
        "frame-shift",
        "nonsense",
        "splice-site",
        "no-frame-shift-newStop",
        "CNV+",
        "CNV-",
        "noStart",
    } == set(res)


def test_build_effect_types_bad(
    query_base: EffectTypesMixin,
) -> None:
    effect_types = "LGDs, not-an-effect-type"

    with pytest.raises(AssertionError):
        query_base.build_effect_types(effect_types)


def test_build_effect_types_bad_not_safe(
    query_base: EffectTypesMixin,
) -> None:
    effect_types = "LGDs, not-an-effect-type"

    res = query_base.build_effect_types(effect_types, safe=False)
    assert {
        "frame-shift",
        "nonsense",
        "splice-site",
        "no-frame-shift-newStop",
    } == set(res)
