# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.effect_annotation.effect import EffectTypesMixin


def test_nonsynonymous_group() -> None:
    effect_groups = ["Nonsynonymous"]
    effects = EffectTypesMixin.build_effect_types(effect_groups)

    assert set(effects) == {
        "nonsense", "frame-shift", "splice-site", "no-frame-shift-newStop",
        "missense", "no-frame-shift", "noStart", "noEnd"}
