'''
Created on Feb 27, 2018

@author: lubo
'''
import numpy as np
from variants.variant import FamilyVariant


def test_denovo_check():
    # AA, AA -> AC
    assert FamilyVariant.check_denovo_trio(
        np.array([0, 1]),
        np.array([0, 0]),
        np.array([0, 0])
    )

    # AA, AA -> CA
    assert FamilyVariant.check_denovo_trio(
        np.array([1, 0]),
        np.array([0, 0]),
        np.array([0, 0])
    )

    # CC, CC -> CA
    assert FamilyVariant.check_denovo_trio(
        np.array([1, 0]),
        np.array([1, 1]),
        np.array([1, 1])
    )

    # CC, CC -> AA
    assert FamilyVariant.check_denovo_trio(
        np.array([0, 0]),
        np.array([1, 1]),
        np.array([1, 1])
    )

    # GG, GG -> AC
    assert FamilyVariant.check_denovo_trio(
        np.array([0, 1]),
        np.array([2, 2]),
        np.array([2, 2])
    )

    # CC,CC -> GC
    assert FamilyVariant.check_denovo_trio(
        np.array([2, 1]),
        np.array([1, 1]),
        np.array([1, 1])
    )


def test_omission_check():
    # CC, AA -> AA
    assert FamilyVariant.check_omission_trio(
        np.array([0, 0]),
        np.array([1, 1]),
        np.array([0, 0])
    )

    # AA, CC -> AA
    assert FamilyVariant.check_omission_trio(
        np.array([0, 0]),
        np.array([0, 0]),
        np.array([1, 1])
    )

    # AA,CC -> CC
    assert FamilyVariant.check_omission_trio(
        np.array([1, 1]),
        np.array([0, 0]),
        np.array([1, 1])
    )

    # AA,CC -> CC
    assert FamilyVariant.check_omission_trio(
        np.array([1, 1]),
        np.array([1, 1]),
        np.array([0, 0])
    )


def test_mixed_check_1():
    # AA,CC -> GG
    trio = [
        np.array([2, 2]),
        np.array([1, 1]),
        np.array([0, 0])
    ]
    assert FamilyVariant.check_denovo_trio(*trio)
    assert not FamilyVariant.check_omission_trio(*trio)
    assert not FamilyVariant.check_mendelian_trio(*trio)


def test_mixed_check_2():
    # AA,CC -> AG
    trio = [
        np.array([2, 1]),
        np.array([1, 1]),
        np.array([0, 0])
    ]
    assert FamilyVariant.check_denovo_trio(*trio)
    assert not FamilyVariant.check_omission_trio(*trio)
    assert not FamilyVariant.check_mendelian_trio(*trio)


def test_mixed_check_3():
    # AA,CC -> AA
    trio = [
        np.array([0, 0]),  # ch
        np.array([1, 1]),  # p1
        np.array([0, 0])   # p2
    ]
    assert FamilyVariant.check_omission_trio(*trio)
    assert not FamilyVariant.check_denovo_trio(*trio)
    assert not FamilyVariant.check_mendelian_trio(*trio)


def test_mixed_check_4():
    # AA,CC -> AG
    trio = [
        np.array([0, 2]),  # ch
        np.array([1, 1]),  # p1
        np.array([0, 0])   # p2
    ]
    assert FamilyVariant.check_denovo_trio(*trio)
    assert not FamilyVariant.check_omission_trio(*trio)
    assert not FamilyVariant.check_mendelian_trio(*trio)
