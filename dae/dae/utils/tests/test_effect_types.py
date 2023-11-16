# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from dae.effect_annotation.effect import EffectTypesMixin


@pytest.fixture(scope="session")
def query_base(request):
    query = EffectTypesMixin()
    return query


def test_build_effect_types(query_base):
    effect_types = "Frame-shift,Nonsense,Splice-site,Non coding"

    res = query_base.build_effect_types(effect_types)
    assert res is not None
    assert ["frame-shift", "nonsense", "splice-site", "non-coding"] == res


def test_build_effect_types_lgds(query_base):
    effect_types = "LGDs"

    res = query_base.build_effect_types(effect_types)
    assert res is not None
    assert set(
        ["frame-shift", "nonsense", "splice-site", "no-frame-shift-newStop"]
    ) == set(res)


def test_build_effect_types_mixed(query_base):
    effect_types = "LGDs,CNV, noStart"

    res = query_base.build_effect_types(effect_types)
    assert res is not None
    assert set(
        [
            "frame-shift",
            "nonsense",
            "splice-site",
            "no-frame-shift-newStop",
            "CNV+",
            "CNV-",
            "noStart",
        ]
    ) == set(res)


def test_build_effect_types_bad(query_base):
    effect_types = "LGDs, not-an-effect-type"

    with pytest.raises(AssertionError):
        query_base.build_effect_types(effect_types)


def test_build_effect_types_bad_not_safe(query_base):
    effect_types = "LGDs, not-an-effect-type"

    res = query_base.build_effect_types(effect_types, safe=False)
    assert set(
        ["frame-shift", "nonsense", "splice-site", "no-frame-shift-newStop"]
    ) == set(res)


def test_build_effect_types_naming(query_base):
    effect_types_arguments = [
        ("nonsense", ["Nonsense"]),
        (["nonsense"], ["Nonsense"]),
        (
            ["frame-shift", "nonsense", "splice-site"],
            ["Frame-shift", "Nonsense", "Splice-site"],
        ),
        (["noStart"], ["noStart"]),
        (["Synonymous"], ["Synonymous"]),
        (["Intron"], ["Intron"]),
        ("non-coding", ["Non coding"]),
    ]

    for effect_types, should_become in effect_types_arguments:
        result = query_base.build_effect_types_naming(effect_types)
        assert result == should_become


def test_build_effect_types_naming_should_raise(query_base):
    effect_types_arguments = [["ala bala"]]
    for effect_types in effect_types_arguments:
        with pytest.raises(AssertionError):
            query_base.build_effect_types_naming(effect_types, safe=True)

    for effect_types in effect_types_arguments:
        result = query_base.build_effect_types_naming(effect_types, safe=False)
        assert result == effect_types
