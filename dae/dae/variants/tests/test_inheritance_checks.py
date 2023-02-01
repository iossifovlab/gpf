# pylint: disable=W0621,C0114,C0116,W0212,W0613
import numpy as np
from dae.variants.family_variant import FamilyAllele as FV


def test_denovo_check_1():
    # AA, AA -> AC
    assert FV.check_denovo_trio(
        np.array([0, 0]), np.array([0, 0]), np.array([0, 1]), 1
    )
    assert not FV.check_denovo_trio(
        np.array([0, 0]), np.array([0, 0]), np.array([0, 1]), 0
    )


def test_denovo_check_2():
    # AA, AA -> CA
    assert FV.check_denovo_trio(
        np.array([0, 0]), np.array([0, 0]), np.array([1, 0]), 1
    )
    assert not FV.check_denovo_trio(
        np.array([0, 0]), np.array([0, 0]), np.array([1, 0]), 0
    )


def test_denovo_check_3():
    # CC, CC -> CA
    assert FV.check_denovo_trio(
        np.array([1, 1]), np.array([1, 1]), np.array([1, 0]), 0
    )
    assert not FV.check_denovo_trio(
        np.array([1, 1]), np.array([1, 1]), np.array([1, 0]), 1
    )


def test_denovo_check_4():
    # CC, CC -> AA
    assert FV.check_denovo_trio(
        np.array([1, 1]), np.array([1, 1]), np.array([0, 0]), 0
    )
    assert not FV.check_denovo_trio(
        np.array([1, 1]), np.array([1, 1]), np.array([0, 0]), 1
    )


def test_denovo_check_5():
    # GG, GG -> AC
    assert FV.check_denovo_trio(
        np.array([2, 2]), np.array([2, 2]), np.array([0, 1]), 0
    )
    assert FV.check_denovo_trio(
        np.array([2, 2]), np.array([2, 2]), np.array([0, 1]), 1
    )
    assert not FV.check_denovo_trio(
        np.array([2, 2]), np.array([2, 2]), np.array([0, 1]), 2
    )


def test_denovo_check_6():
    # CC,CC -> GC
    assert FV.check_denovo_trio(
        np.array([1, 1]), np.array([1, 1]), np.array([2, 1]), 2
    )
    assert not FV.check_denovo_trio(
        np.array([1, 1]), np.array([1, 1]), np.array([2, 1]), 1
    )
    assert not FV.check_denovo_trio(
        np.array([1, 1]), np.array([1, 1]), np.array([2, 1]), 0
    )


def test_omission_check_1():
    # CC, AA -> AA
    assert FV.check_omission_trio(
        np.array([1, 1]), np.array([0, 0]), np.array([0, 0]), 1
    )
    assert not FV.check_omission_trio(
        np.array([1, 1]), np.array([0, 0]), np.array([0, 0]), 0
    )
    assert not FV.check_denovo_trio(
        np.array([1, 1]), np.array([0, 0]), np.array([0, 0]), 0
    )
    assert not FV.check_denovo_trio(
        np.array([1, 1]), np.array([0, 0]), np.array([0, 0]), 1
    )


def test_omission_check_2():
    # AA, CC -> AA
    assert FV.check_omission_trio(
        np.array([0, 0]), np.array([1, 1]), np.array([0, 0]), 1
    )
    assert not FV.check_omission_trio(
        np.array([0, 0]), np.array([1, 1]), np.array([0, 0]), 0
    )


def test_omission_check_3():
    # AA,CC -> CC
    assert FV.check_omission_trio(
        np.array([0, 0]), np.array([1, 1]), np.array([1, 1]), 0
    )
    assert not FV.check_omission_trio(
        np.array([0, 0]), np.array([1, 1]), np.array([1, 1]), 1
    )


def test_omission_check_4():
    # AA,CC -> CC
    assert FV.check_omission_trio(
        np.array([1, 1]), np.array([0, 0]), np.array([1, 1]), 0
    )
    assert not FV.check_omission_trio(
        np.array([1, 1]), np.array([0, 0]), np.array([1, 1]), 1
    )


def test_omission_not_denovo():
    # AA,CC -> AA
    trio = [
        np.array([0, 0]),  # p1
        np.array([1, 1]),  # p2
        np.array([0, 0]),  # ch
    ]
    assert FV.check_omission_trio(*trio, allele_index=1)
    assert not FV.check_denovo_trio(*trio, allele_index=1)
    assert not FV.check_mendelian_trio(*trio, allele_index=1)

    # FIXME:
    assert not FV.check_omission_trio(*trio, allele_index=0)
    assert not FV.check_denovo_trio(*trio, allele_index=0)
    assert FV.check_mendelian_trio(*trio, allele_index=0)


def test_mendelian_from_ivan_1():
    # AC AA AA mendel
    assert FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([0, 0]), 0
    )

    assert not FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([0, 0]), 1
    )


def test_mendelian_from_ivan_2():
    # AC AA AC mendel
    assert FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([0, 1]), 0
    )

    assert FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([0, 1]), 1
    )


def test_mendelian_from_ivan_3():
    # AC AC AA mendel
    assert FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([0, 0]), 0
    )
    assert not FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([0, 0]), 1
    )


def test_mendelian_from_ivan_4():
    # AC AC AC mendel
    assert FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([0, 1]), 0
    )
    assert FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([0, 1]), 1
    )


def test_mendelian_from_ivan_5():
    # AC AC CC mendel
    assert FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([1, 1]), 1
    )
    assert not FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([1, 1]), 0
    )


def test_denovo_and_omission_from_ivan_1():
    # AA AA AC denovo
    assert FV.check_denovo_trio(
        np.array([0, 0]), np.array([0, 0]), np.array([0, 1]), 1
    )
    assert not FV.check_denovo_trio(
        np.array([0, 0]), np.array([0, 0]), np.array([0, 1]), 0
    )


def test_denovo_and_omission_from_ivan_2():
    # AC AA CC omission
    assert FV.check_omission_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([1, 1]), 0
    )
    assert not FV.check_omission_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([1, 1]), 1
    )


def test_denovo_and_omission_from_ivan_3():
    # AA CC AA omission
    assert FV.check_omission_trio(
        np.array([0, 0]), np.array([1, 1]), np.array([0, 0]), 1
    )
    assert not FV.check_omission_trio(
        np.array([0, 0]), np.array([1, 1]), np.array([0, 0]), 0
    )


def test_denovo_and_omission_from_ivan_4():
    # AA CC CC omission
    assert FV.check_omission_trio(
        np.array([0, 0]), np.array([1, 1]), np.array([1, 1]), 0
    )
    assert not FV.check_omission_trio(
        np.array([0, 0]), np.array([1, 1]), np.array([1, 1]), 1
    )


def test_weird_mendel_from_ivan_1():
    # AC AT AA mendel
    assert FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 2]), np.array([0, 0]), 0
    )
    assert not FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 2]), np.array([0, 0]), 1
    )
    assert not FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 2]), np.array([0, 0]), 2
    )


def test_weird_mendel_from_ivan_2():
    # AC AT AT mendel
    assert FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 2]), np.array([0, 2]), 0
    )
    assert not FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 2]), np.array([0, 2]), 1
    )
    assert FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 2]), np.array([0, 2]), 2
    )


def test_weird_mendel_from_ivan_3():
    # AC AT AC mendel
    assert FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 2]), np.array([0, 1]), 0
    )
    assert FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 2]), np.array([0, 1]), 1
    )
    assert not FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 2]), np.array([0, 1]), 2
    )


def test_weird_mendel_from_ivan_4():
    # AC AT CT mendel
    assert not FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 2]), np.array([1, 2]), 0
    )
    assert FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 2]), np.array([1, 2]), 1
    )
    assert FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 2]), np.array([1, 2]), 2
    )


def test_weird_denovo_from_ivan_1_1():
    # AA AC AG denovo
    assert FV.check_denovo_trio(
        np.array([0, 0]), np.array([0, 1]), np.array([0, 2]), 2
    )
    assert not FV.check_denovo_trio(
        np.array([0, 0]), np.array([0, 1]), np.array([0, 2]), 0
    )
    assert not FV.check_denovo_trio(
        np.array([0, 0]), np.array([0, 1]), np.array([0, 2]), 1
    )
    assert not FV.check_omission_trio(
        np.array([0, 0]), np.array([0, 1]), np.array([0, 2]), 0
    )
    assert not FV.check_omission_trio(
        np.array([0, 0]), np.array([0, 1]), np.array([0, 2]), 1
    )
    assert not FV.check_omission_trio(
        np.array([0, 0]), np.array([0, 1]), np.array([0, 2]), 2
    )


def test_weird_denovo_from_ivan_1_2():
    # AC AA AG denovo
    assert FV.check_denovo_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([0, 2]), 2
    )
    assert not FV.check_denovo_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([0, 2]), 0
    )
    assert not FV.check_denovo_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([0, 2]), 1
    )
    assert not FV.check_omission_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([0, 2]), 2
    )
    assert not FV.check_omission_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([0, 2]), 0
    )
    assert not FV.check_omission_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([0, 2]), 1
    )


def test_weird_denovo_from_ivan_1_3():
    # AA AC GA denovo
    assert FV.check_denovo_trio(
        np.array([0, 0]), np.array([0, 1]), np.array([2, 0]), 2
    )
    assert not FV.check_denovo_trio(
        np.array([0, 0]), np.array([0, 1]), np.array([2, 0]), 0
    )
    assert not FV.check_denovo_trio(
        np.array([0, 0]), np.array([0, 1]), np.array([2, 0]), 1
    )
    assert not FV.check_omission_trio(
        np.array([0, 0]), np.array([0, 1]), np.array([2, 0]), 2
    )
    assert not FV.check_omission_trio(
        np.array([0, 0]), np.array([0, 1]), np.array([2, 0]), 0
    )
    assert not FV.check_omission_trio(
        np.array([0, 0]), np.array([0, 1]), np.array([2, 0]), 1
    )


def test_weird_denovo_from_ivan_1_4():
    # AC AA GA denovo
    assert FV.check_denovo_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([2, 0]), 2
    )
    assert not FV.check_denovo_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([2, 0]), 0
    )
    assert not FV.check_denovo_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([2, 0]), 1
    )
    assert not FV.check_omission_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([2, 0]), 2
    )
    assert not FV.check_omission_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([2, 0]), 0
    )
    assert not FV.check_omission_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([2, 0]), 1
    )


def test_weird_denovo_from_ivan_3():
    # AC AC AG denovo
    assert FV.check_denovo_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([0, 2]), 2
    )
    assert not FV.check_denovo_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([0, 2]), 0
    )
    assert not FV.check_denovo_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([0, 2]), 1
    )
    assert not FV.check_omission_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([0, 2]), 2
    )
    assert not FV.check_omission_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([0, 2]), 0
    )
    assert not FV.check_omission_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([0, 2]), 1
    )


def test_weird_denovo_from_ivan_4():
    # AC AC CG denovo
    assert FV.check_denovo_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([1, 2]), 2
    )
    assert not FV.check_denovo_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([1, 2]), 0
    )
    assert not FV.check_denovo_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([1, 2]), 1
    )
    assert not FV.check_omission_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([1, 2]), 2
    )
    assert not FV.check_omission_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([1, 2]), 0
    )
    assert not FV.check_omission_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([1, 2]), 1
    )


def test_super_weird_denovo_omission_mix_from_ivan_1():
    # AC AA TG denovo
    trio = [
        np.array([0, 1]),
        np.array([0, 0]),
        np.array([2, 3]),
    ]
    assert FV.check_omission_trio(*trio, allele_index=0)
    assert not FV.check_omission_trio(*trio, allele_index=1)
    assert not FV.check_omission_trio(*trio, allele_index=2)
    assert not FV.check_omission_trio(*trio, allele_index=3)

    assert not FV.check_denovo_trio(*trio, allele_index=0)
    assert not FV.check_denovo_trio(*trio, allele_index=1)
    assert FV.check_denovo_trio(*trio, allele_index=2)
    assert FV.check_denovo_trio(*trio, allele_index=3)
    # assert FV.calc_inheritance_trio(*trio) == Inheritance.denovo


def test_super_weird_denovo_omission_mix_from_ivan_2():
    # AA AC TG denovo
    trio = [
        np.array([0, 0]),
        np.array([0, 1]),
        np.array([2, 3]),
    ]
    assert FV.check_omission_trio(*trio, allele_index=0)
    assert not FV.check_omission_trio(*trio, allele_index=1)
    assert not FV.check_omission_trio(*trio, allele_index=2)
    assert not FV.check_omission_trio(*trio, allele_index=3)

    assert not FV.check_denovo_trio(*trio, allele_index=0)
    assert not FV.check_denovo_trio(*trio, allele_index=1)
    assert FV.check_denovo_trio(*trio, allele_index=2)
    assert FV.check_denovo_trio(*trio, allele_index=3)
    # assert FV.calc_inheritance_trio(*trio) == Inheritance.denovo


def test_mixed_check_1():
    # AA,CC -> GG
    trio = [
        np.array([1, 1]),
        np.array([0, 0]),
        np.array([2, 2]),
    ]
    assert not FV.check_denovo_trio(*trio, allele_index=0)
    assert not FV.check_denovo_trio(*trio, allele_index=1)
    assert FV.check_denovo_trio(*trio, allele_index=2)

    assert FV.check_omission_trio(*trio, allele_index=0)
    assert FV.check_omission_trio(*trio, allele_index=1)
    assert not FV.check_omission_trio(*trio, allele_index=2)

    assert not FV.check_mendelian_trio(*trio, allele_index=0)
    assert not FV.check_mendelian_trio(*trio, allele_index=1)
    assert not FV.check_mendelian_trio(*trio, allele_index=2)


def test_mixed_check_2():
    # AA,CC -> AG
    trio = [
        np.array([1, 1]),
        np.array([0, 0]),
        np.array([2, 1]),
    ]
    assert not FV.check_denovo_trio(*trio, allele_index=0)
    assert not FV.check_denovo_trio(*trio, allele_index=1)
    assert FV.check_denovo_trio(*trio, allele_index=2)

    assert FV.check_omission_trio(*trio, allele_index=0)
    assert not FV.check_omission_trio(*trio, allele_index=1)
    assert not FV.check_omission_trio(*trio, allele_index=2)

    assert not FV.check_mendelian_trio(*trio, allele_index=0)
    assert FV.check_mendelian_trio(*trio, allele_index=1)
    assert not FV.check_mendelian_trio(*trio, allele_index=2)


def test_mixed_check_4():
    # AA,CC -> AG
    trio = [
        np.array([1, 1]),  # p1
        np.array([0, 0]),  # p2
        np.array([0, 2]),  # ch
    ]
    assert not FV.check_denovo_trio(*trio, allele_index=0)
    assert not FV.check_denovo_trio(*trio, allele_index=1)
    assert FV.check_denovo_trio(*trio, allele_index=2)

    assert not FV.check_omission_trio(*trio, allele_index=0)
    assert FV.check_omission_trio(*trio, allele_index=1)
    assert not FV.check_omission_trio(*trio, allele_index=2)

    assert FV.check_mendelian_trio(*trio, allele_index=0)
    assert not FV.check_mendelian_trio(*trio, allele_index=1)
    assert not FV.check_mendelian_trio(*trio, allele_index=2)
