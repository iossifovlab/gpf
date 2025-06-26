# pylint: disable=redefined-outer-name,C0114,C0116,protected-access,fixme

import pytest
from dae.variants.attributes import Inheritance, bitmask2inheritance


@pytest.mark.parametrize("bitmask, expected", [
    (388, {
        Inheritance.denovo, Inheritance.missing, Inheritance.unknown}),
    (386, {
        Inheritance.mendelian, Inheritance.missing, Inheritance.unknown}),
    (384, {
        Inheritance.missing, Inheritance.unknown}),
    (258, {
        Inheritance.mendelian, Inheritance.unknown}),
    (260, {
        Inheritance.denovo, Inheritance.unknown}),
    (290, {
        Inheritance.possible_omission, Inheritance.mendelian,
        Inheritance.unknown}),
    (8, {
        Inheritance.possible_denovo}),
    (32, {
        Inheritance.possible_omission}),
    (150, {
        Inheritance.omission, Inheritance.denovo,
        Inheritance.missing, Inheritance.mendelian}),
    (290 & 32, {
        Inheritance.possible_omission}),
])
def test_bitmask2inheritance(
    bitmask: int,
    expected: set[Inheritance],
) -> None:
    assert bitmask2inheritance(bitmask) == expected
