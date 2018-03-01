'''
Created on Feb 27, 2018

@author: lubo
'''
import numpy as np
from variants.variant import FamilyVariant
from variants.attributes import Inheritance


def test_denovo_check():
    # AA, AA -> AC
    assert FamilyVariant.check_denovo_trio(
        np.array([0, 0]),
        np.array([0, 0]),
        np.array([0, 1]),
    )

    # AA, AA -> CA
    assert FamilyVariant.check_denovo_trio(
        np.array([0, 0]),
        np.array([0, 0]),
        np.array([1, 0]),
    )

    # CC, CC -> CA
    assert FamilyVariant.check_denovo_trio(
        np.array([1, 1]),
        np.array([1, 1]),
        np.array([1, 0]),
    )

    # CC, CC -> AA
    assert FamilyVariant.check_denovo_trio(
        np.array([1, 1]),
        np.array([1, 1]),
        np.array([0, 0]),
    )

    # GG, GG -> AC
    assert FamilyVariant.check_denovo_trio(
        np.array([2, 2]),
        np.array([2, 2]),
        np.array([0, 1]),
    )

    # CC,CC -> GC
    assert FamilyVariant.check_denovo_trio(
        np.array([1, 1]),
        np.array([1, 1]),
        np.array([2, 1]),
    )


def test_omission_check():
    # CC, AA -> AA
    assert FamilyVariant.check_omission_trio(
        np.array([1, 1]),
        np.array([0, 0]),
        np.array([0, 0]),
    )
    assert not FamilyVariant.check_denovo_trio(
        np.array([1, 1]),
        np.array([0, 0]),
        np.array([0, 0]),
    )

    # AA, CC -> AA
    assert FamilyVariant.check_omission_trio(
        np.array([0, 0]),
        np.array([1, 1]),
        np.array([0, 0]),
    )

    # AA,CC -> CC
    assert FamilyVariant.check_omission_trio(
        np.array([0, 0]),
        np.array([1, 1]),
        np.array([1, 1]),
    )

    # AA,CC -> CC
    assert FamilyVariant.check_omission_trio(
        np.array([1, 1]),
        np.array([0, 0]),
        np.array([1, 1]),
    )


def test_omission_not_denovo():
    # AA,CC -> AA
    trio = [
        np.array([0, 0]),  # p1
        np.array([1, 1]),  # p2
        np.array([0, 0]),  # ch
    ]
    assert FamilyVariant.check_omission_trio(*trio)
    assert not FamilyVariant.check_denovo_trio(*trio)
    assert not FamilyVariant.check_mendelian_trio(*trio)


def test_mendelian_from_ivan():
    # AC AA AA mendel
    assert FamilyVariant.check_mendelian_trio(
        np.array([0, 1]),
        np.array([0, 0]),
        np.array([0, 0]),
    )

    # AC AA AC mendel
    assert FamilyVariant.check_mendelian_trio(
        np.array([0, 1]),
        np.array([0, 0]),
        np.array([0, 1]),
    )

    # AC AC AA mendel
    assert FamilyVariant.check_mendelian_trio(
        np.array([0, 1]),
        np.array([0, 1]),
        np.array([0, 0]),
    )

    # AC AC AC mendel
    assert FamilyVariant.check_mendelian_trio(
        np.array([0, 1]),
        np.array([0, 1]),
        np.array([0, 1]),
    )

    # AC AC CC mendel
    assert FamilyVariant.check_mendelian_trio(
        np.array([0, 1]),
        np.array([0, 1]),
        np.array([1, 1]),
    )


def test_denovo_and_omission_from_ivan():
    # AA AA AC denovo
    assert FamilyVariant.check_denovo_trio(
        np.array([0, 0]),
        np.array([0, 0]),
        np.array([0, 1]),
    )

    # AC AA CC omission
    assert FamilyVariant.check_omission_trio(
        np.array([0, 1]),
        np.array([0, 0]),
        np.array([1, 1]),
    )

    # AA CC AA omission
    assert FamilyVariant.check_omission_trio(
        np.array([0, 0]),
        np.array([1, 1]),
        np.array([0, 0]),
    )

    # AA CC CC omission
    assert FamilyVariant.check_omission_trio(
        np.array([0, 0]),
        np.array([1, 1]),
        np.array([1, 1]),
    )


def test_weird_mendel_from_ivan():
    # AC AT AA mendel
    assert FamilyVariant.check_mendelian_trio(
        np.array([0, 1]),
        np.array([0, 2]),
        np.array([0, 0]),
    )

    # AC AT AT mendel
    assert FamilyVariant.check_mendelian_trio(
        np.array([0, 1]),
        np.array([0, 2]),
        np.array([0, 2]),
    )

    # AC AT AC mendel
    assert FamilyVariant.check_mendelian_trio(
        np.array([0, 1]),
        np.array([0, 2]),
        np.array([0, 1]),
    )

    # AC AT CT mendel
    assert FamilyVariant.check_mendelian_trio(
        np.array([0, 1]),
        np.array([0, 2]),
        np.array([1, 2]),
    )


def test_weird_denovo_from_ivan_1():
    # AA AC AG denovo
    assert FamilyVariant.check_denovo_trio(
        np.array([0, 0]),
        np.array([0, 1]),
        np.array([0, 2]),
    )
    assert not FamilyVariant.check_omission_trio(
        np.array([0, 0]),
        np.array([0, 1]),
        np.array([0, 2]),
    )

    # AC AA AG denovo
    assert FamilyVariant.check_denovo_trio(
        np.array([0, 1]),
        np.array([0, 0]),
        np.array([0, 2]),
    )
    assert not FamilyVariant.check_omission_trio(
        np.array([0, 1]),
        np.array([0, 0]),
        np.array([0, 2]),
    )

    # AA AC GA denovo
    assert FamilyVariant.check_denovo_trio(
        np.array([0, 0]),
        np.array([0, 1]),
        np.array([2, 0]),
    )
    assert not FamilyVariant.check_omission_trio(
        np.array([0, 0]),
        np.array([0, 1]),
        np.array([2, 0]),
    )

    # AC AA GA denovo
    assert FamilyVariant.check_denovo_trio(
        np.array([0, 1]),
        np.array([0, 0]),
        np.array([2, 0]),
    )
    assert not FamilyVariant.check_omission_trio(
        np.array([0, 1]),
        np.array([0, 0]),
        np.array([2, 0]),
    )


def test_weird_denovo_from_ivan_3():
    # AC AC AG denovo
    assert FamilyVariant.check_denovo_trio(
        np.array([0, 1]),
        np.array([0, 1]),
        np.array([0, 2]),
    )
    assert not FamilyVariant.check_omission_trio(
        np.array([0, 1]),
        np.array([0, 1]),
        np.array([0, 2]),
    )


def test_weird_denovo_from_ivan_4():
    # AC AC CG denovo
    assert FamilyVariant.check_denovo_trio(
        np.array([0, 1]),
        np.array([0, 1]),
        np.array([1, 2]),
    )
    assert not FamilyVariant.check_omission_trio(
        np.array([0, 1]),
        np.array([0, 1]),
        np.array([1, 2]),
    )


def test_super_weird_denovo_omission_mix_from_ivan():
    # AC AA TG denovo
    trio = [
        np.array([0, 1]),
        np.array([0, 0]),
        np.array([2, 3]),
    ]
    assert FamilyVariant.check_omission_trio(*trio)
    assert FamilyVariant.check_denovo_trio(*trio)
    assert FamilyVariant.calc_inheritance_trio(*trio) == Inheritance.denovo

    # AA AC TG denovo
    trio = [
        np.array([0, 0]),
        np.array([0, 1]),
        np.array([2, 3]),
    ]
    assert FamilyVariant.check_omission_trio(*trio)
    assert FamilyVariant.check_denovo_trio(*trio)
    assert FamilyVariant.calc_inheritance_trio(*trio) == Inheritance.denovo


# @pytest.mark.skip(reason="discuss with Ivan what is this?")
def test_mixed_check_1():
    # AA,CC -> GG
    trio = [
        np.array([1, 1]),
        np.array([0, 0]),
        np.array([2, 2]),
    ]
    assert FamilyVariant.check_denovo_trio(*trio)
    assert FamilyVariant.check_omission_trio(*trio)
    assert not FamilyVariant.check_mendelian_trio(*trio)


# @pytest.mark.skip(reason="discuss with Ivan what is this?")
def test_mixed_check_2():
    # AA,CC -> AG
    trio = [
        np.array([1, 1]),
        np.array([0, 0]),
        np.array([2, 1]),
    ]
    assert FamilyVariant.check_denovo_trio(*trio)
    assert FamilyVariant.check_omission_trio(*trio)
    assert not FamilyVariant.check_mendelian_trio(*trio)


# @pytest.mark.skip(reason="discuss with Ivan what is this?")
def test_mixed_check_4():
    # AA,CC -> AG
    trio = [
        np.array([1, 1]),  # p1
        np.array([0, 0]),  # p2
        np.array([0, 2]),  # ch
    ]
    assert FamilyVariant.check_denovo_trio(*trio)
    assert FamilyVariant.check_omission_trio(*trio)
    assert not FamilyVariant.check_mendelian_trio(*trio)
