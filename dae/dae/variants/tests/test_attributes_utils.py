# pylint: disable=redefined-outer-name,C0114,C0116,protected-access,fixme

import pytest

from dae.variants.attributes import bitmask2inheritance, Inheritance


@pytest.mark.parametrize("bitmask, expected", [
    (388, set([
        Inheritance.denovo, Inheritance.missing, Inheritance.unknown])),
    (386, set([
        Inheritance.mendelian, Inheritance.missing, Inheritance.unknown])),
    (384, set([
        Inheritance.missing, Inheritance.unknown])),
    (258, set([
        Inheritance.mendelian, Inheritance.unknown])),
    (260, set([
        Inheritance.denovo, Inheritance.unknown])),
    (290, set([
        Inheritance.possible_omission, Inheritance.mendelian,
        Inheritance.unknown])),
    (8, set([
        Inheritance.possible_denovo, ])),
    (32, set([
        Inheritance.possible_omission, ])),
    (150, set([
        Inheritance.omission, Inheritance.denovo,
        Inheritance.missing, Inheritance.mendelian, ])),
    (290 & 32, set([
        Inheritance.possible_omission, ])),
])
def test_bitmask2inheritance(bitmask, expected):
    assert bitmask2inheritance(bitmask) == expected
