# pylint: disable=W0621,C0114,C0116,W0212,W0613
import numpy as np

from dae.variants.family_variant import FamilyAllele as FV


def test_denovo_check_1() -> None:
    # AA, AA -> AC
    assert FV.check_denovo_trio(
        np.array([0, 0]), np.array([0, 0]), np.array([0, 1]), 1,
    )
    assert not FV.check_denovo_trio(
        np.array([0, 0]), np.array([0, 0]), np.array([0, 1]), 0,
    )


def test_denovo_check_2() -> None:
    # AA, AA -> CA
    assert FV.check_denovo_trio(
        np.array([0, 0]), np.array([0, 0]), np.array([1, 0]), 1,
    )
    assert not FV.check_denovo_trio(
        np.array([0, 0]), np.array([0, 0]), np.array([1, 0]), 0,
    )


def test_denovo_check_3() -> None:
    # CC, CC -> CA
    assert FV.check_denovo_trio(
        np.array([1, 1]), np.array([1, 1]), np.array([1, 0]), 0,
    )
    assert not FV.check_denovo_trio(
        np.array([1, 1]), np.array([1, 1]), np.array([1, 0]), 1,
    )


def test_denovo_check_4() -> None:
    # CC, CC -> AA
    assert FV.check_denovo_trio(
        np.array([1, 1]), np.array([1, 1]), np.array([0, 0]), 0,
    )
    assert not FV.check_denovo_trio(
        np.array([1, 1]), np.array([1, 1]), np.array([0, 0]), 1,
    )


def test_denovo_check_5() -> None:
    # GG, GG -> AC
    assert FV.check_denovo_trio(
        np.array([2, 2]), np.array([2, 2]), np.array([0, 1]), 0,
    )
    assert FV.check_denovo_trio(
        np.array([2, 2]), np.array([2, 2]), np.array([0, 1]), 1,
    )
    assert not FV.check_denovo_trio(
        np.array([2, 2]), np.array([2, 2]), np.array([0, 1]), 2,
    )


def test_denovo_check_6() -> None:
    # CC,CC -> GC
    assert FV.check_denovo_trio(
        np.array([1, 1]), np.array([1, 1]), np.array([2, 1]), 2,
    )
    assert not FV.check_denovo_trio(
        np.array([1, 1]), np.array([1, 1]), np.array([2, 1]), 1,
    )
    assert not FV.check_denovo_trio(
        np.array([1, 1]), np.array([1, 1]), np.array([2, 1]), 0,
    )


def test_omission_check_1() -> None:
    # CC, AA -> AA
    assert FV.check_omission_trio(
        np.array([1, 1]), np.array([0, 0]), np.array([0, 0]), 1,
    )
    assert not FV.check_omission_trio(
        np.array([1, 1]), np.array([0, 0]), np.array([0, 0]), 0,
    )
    assert not FV.check_denovo_trio(
        np.array([1, 1]), np.array([0, 0]), np.array([0, 0]), 0,
    )
    assert not FV.check_denovo_trio(
        np.array([1, 1]), np.array([0, 0]), np.array([0, 0]), 1,
    )


def test_omission_check_2() -> None:
    # AA, CC -> AA
    assert FV.check_omission_trio(
        np.array([0, 0]), np.array([1, 1]), np.array([0, 0]), 1,
    )
    assert not FV.check_omission_trio(
        np.array([0, 0]), np.array([1, 1]), np.array([0, 0]), 0,
    )


def test_omission_check_3() -> None:
    # AA,CC -> CC
    assert FV.check_omission_trio(
        np.array([0, 0]), np.array([1, 1]), np.array([1, 1]), 0,
    )
    assert not FV.check_omission_trio(
        np.array([0, 0]), np.array([1, 1]), np.array([1, 1]), 1,
    )


def test_omission_check_4() -> None:
    # AA,CC -> CC
    assert FV.check_omission_trio(
        np.array([1, 1]), np.array([0, 0]), np.array([1, 1]), 0,
    )
    assert not FV.check_omission_trio(
        np.array([1, 1]), np.array([0, 0]), np.array([1, 1]), 1,
    )


def test_omission_not_denovo() -> None:
    # AA,CC -> AA
    trio = [
        np.array([0, 0]),  # p1
        np.array([1, 1]),  # p2
        np.array([0, 0]),  # ch
    ]
    assert FV.check_omission_trio(
        trio[0], trio[1], trio[2], allele_index=1)
    assert not FV.check_denovo_trio(
        trio[0], trio[1], trio[2], allele_index=1)
    assert not FV.check_mendelian_trio(
        trio[0], trio[1], trio[2], allele_index=1)

    # FIXME:
    assert not FV.check_omission_trio(
        trio[0], trio[1], trio[2], allele_index=0)
    assert not FV.check_denovo_trio(
        trio[0], trio[1], trio[2], allele_index=0)
    assert FV.check_mendelian_trio(
        trio[0], trio[1], trio[2], allele_index=0)


def test_mendelian_from_ivan_1() -> None:
    # AC AA AA mendel
    assert FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([0, 0]), 0,
    )

    assert not FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([0, 0]), 1,
    )


def test_mendelian_from_ivan_2() -> None:
    # AC AA AC mendel
    assert FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([0, 1]), 0,
    )

    assert FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([0, 1]), 1,
    )


def test_mendelian_from_ivan_3() -> None:
    # AC AC AA mendel
    assert FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([0, 0]), 0,
    )
    assert not FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([0, 0]), 1,
    )


def test_mendelian_from_ivan_4() -> None:
    # AC AC AC mendel
    assert FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([0, 1]), 0,
    )
    assert FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([0, 1]), 1,
    )


def test_mendelian_from_ivan_5() -> None:
    # AC AC CC mendel
    assert FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([1, 1]), 1,
    )
    assert not FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([1, 1]), 0,
    )


def test_denovo_and_omission_from_ivan_1() -> None:
    # AA AA AC denovo
    assert FV.check_denovo_trio(
        np.array([0, 0]), np.array([0, 0]), np.array([0, 1]), 1,
    )
    assert not FV.check_denovo_trio(
        np.array([0, 0]), np.array([0, 0]), np.array([0, 1]), 0,
    )


def test_denovo_and_omission_from_ivan_2() -> None:
    # AC AA CC omission
    assert FV.check_omission_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([1, 1]), 0,
    )
    assert not FV.check_omission_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([1, 1]), 1,
    )


def test_denovo_and_omission_from_ivan_3() -> None:
    # AA CC AA omission
    assert FV.check_omission_trio(
        np.array([0, 0]), np.array([1, 1]), np.array([0, 0]), 1,
    )
    assert not FV.check_omission_trio(
        np.array([0, 0]), np.array([1, 1]), np.array([0, 0]), 0,
    )


def test_denovo_and_omission_from_ivan_4() -> None:
    # AA CC CC omission
    assert FV.check_omission_trio(
        np.array([0, 0]), np.array([1, 1]), np.array([1, 1]), 0,
    )
    assert not FV.check_omission_trio(
        np.array([0, 0]), np.array([1, 1]), np.array([1, 1]), 1,
    )


def test_weird_mendel_from_ivan_1() -> None:
    # AC AT AA mendel
    assert FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 2]), np.array([0, 0]), 0,
    )
    assert not FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 2]), np.array([0, 0]), 1,
    )
    assert not FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 2]), np.array([0, 0]), 2,
    )


def test_weird_mendel_from_ivan_2() -> None:
    # AC AT AT mendel
    assert FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 2]), np.array([0, 2]), 0,
    )
    assert not FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 2]), np.array([0, 2]), 1,
    )
    assert FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 2]), np.array([0, 2]), 2,
    )


def test_weird_mendel_from_ivan_3() -> None:
    # AC AT AC mendel
    assert FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 2]), np.array([0, 1]), 0,
    )
    assert FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 2]), np.array([0, 1]), 1,
    )
    assert not FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 2]), np.array([0, 1]), 2,
    )


def test_weird_mendel_from_ivan_4() -> None:
    # AC AT CT mendel
    assert not FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 2]), np.array([1, 2]), 0,
    )
    assert FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 2]), np.array([1, 2]), 1,
    )
    assert FV.check_mendelian_trio(
        np.array([0, 1]), np.array([0, 2]), np.array([1, 2]), 2,
    )


def test_weird_denovo_from_ivan_1_1() -> None:
    # AA AC AG denovo
    assert FV.check_denovo_trio(
        np.array([0, 0]), np.array([0, 1]), np.array([0, 2]), 2,
    )
    assert not FV.check_denovo_trio(
        np.array([0, 0]), np.array([0, 1]), np.array([0, 2]), 0,
    )
    assert not FV.check_denovo_trio(
        np.array([0, 0]), np.array([0, 1]), np.array([0, 2]), 1,
    )
    assert not FV.check_omission_trio(
        np.array([0, 0]), np.array([0, 1]), np.array([0, 2]), 0,
    )
    assert not FV.check_omission_trio(
        np.array([0, 0]), np.array([0, 1]), np.array([0, 2]), 1,
    )
    assert not FV.check_omission_trio(
        np.array([0, 0]), np.array([0, 1]), np.array([0, 2]), 2,
    )


def test_weird_denovo_from_ivan_1_2() -> None:
    # AC AA AG denovo
    assert FV.check_denovo_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([0, 2]), 2,
    )
    assert not FV.check_denovo_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([0, 2]), 0,
    )
    assert not FV.check_denovo_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([0, 2]), 1,
    )
    assert not FV.check_omission_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([0, 2]), 2,
    )
    assert not FV.check_omission_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([0, 2]), 0,
    )
    assert not FV.check_omission_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([0, 2]), 1,
    )


def test_weird_denovo_from_ivan_1_3() -> None:
    # AA AC GA denovo
    assert FV.check_denovo_trio(
        np.array([0, 0]), np.array([0, 1]), np.array([2, 0]), 2,
    )
    assert not FV.check_denovo_trio(
        np.array([0, 0]), np.array([0, 1]), np.array([2, 0]), 0,
    )
    assert not FV.check_denovo_trio(
        np.array([0, 0]), np.array([0, 1]), np.array([2, 0]), 1,
    )
    assert not FV.check_omission_trio(
        np.array([0, 0]), np.array([0, 1]), np.array([2, 0]), 2,
    )
    assert not FV.check_omission_trio(
        np.array([0, 0]), np.array([0, 1]), np.array([2, 0]), 0,
    )
    assert not FV.check_omission_trio(
        np.array([0, 0]), np.array([0, 1]), np.array([2, 0]), 1,
    )


def test_weird_denovo_from_ivan_1_4() -> None:
    # AC AA GA denovo
    assert FV.check_denovo_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([2, 0]), 2,
    )
    assert not FV.check_denovo_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([2, 0]), 0,
    )
    assert not FV.check_denovo_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([2, 0]), 1,
    )
    assert not FV.check_omission_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([2, 0]), 2,
    )
    assert not FV.check_omission_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([2, 0]), 0,
    )
    assert not FV.check_omission_trio(
        np.array([0, 1]), np.array([0, 0]), np.array([2, 0]), 1,
    )


def test_weird_denovo_from_ivan_3() -> None:
    # AC AC AG denovo
    assert FV.check_denovo_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([0, 2]), 2,
    )
    assert not FV.check_denovo_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([0, 2]), 0,
    )
    assert not FV.check_denovo_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([0, 2]), 1,
    )
    assert not FV.check_omission_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([0, 2]), 2,
    )
    assert not FV.check_omission_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([0, 2]), 0,
    )
    assert not FV.check_omission_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([0, 2]), 1,
    )


def test_weird_denovo_from_ivan_4() -> None:
    # AC AC CG denovo
    assert FV.check_denovo_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([1, 2]), 2,
    )
    assert not FV.check_denovo_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([1, 2]), 0,
    )
    assert not FV.check_denovo_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([1, 2]), 1,
    )
    assert not FV.check_omission_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([1, 2]), 2,
    )
    assert not FV.check_omission_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([1, 2]), 0,
    )
    assert not FV.check_omission_trio(
        np.array([0, 1]), np.array([0, 1]), np.array([1, 2]), 1,
    )


def test_super_weird_denovo_omission_mix_from_ivan_1() -> None:
    # AC AA TG denovo
    trio = [
        np.array([0, 1]),
        np.array([0, 0]),
        np.array([2, 3]),
    ]
    assert FV.check_omission_trio(
        trio[0], trio[1], trio[2], allele_index=0)
    assert not FV.check_omission_trio(
        trio[0], trio[1], trio[2], allele_index=1)
    assert not FV.check_omission_trio(
        trio[0], trio[1], trio[2], allele_index=2)
    assert not FV.check_omission_trio(
        trio[0], trio[1], trio[2], allele_index=3)

    assert not FV.check_denovo_trio(
        trio[0], trio[1], trio[2], allele_index=0)
    assert not FV.check_denovo_trio(
        trio[0], trio[1], trio[2], allele_index=1)
    assert FV.check_denovo_trio(
        trio[0], trio[1], trio[2], allele_index=2)
    assert FV.check_denovo_trio(
        trio[0], trio[1], trio[2], allele_index=3)


def test_super_weird_denovo_omission_mix_from_ivan_2() -> None:
    # AA AC TG denovo
    trio = [
        np.array([0, 0]),
        np.array([0, 1]),
        np.array([2, 3]),
    ]
    assert FV.check_omission_trio(
        trio[0], trio[1], trio[2], allele_index=0)
    assert not FV.check_omission_trio(
        trio[0], trio[1], trio[2], allele_index=1)
    assert not FV.check_omission_trio(
        trio[0], trio[1], trio[2], allele_index=2)
    assert not FV.check_omission_trio(
        trio[0], trio[1], trio[2], allele_index=3)

    assert not FV.check_denovo_trio(
        trio[0], trio[1], trio[2], allele_index=0)
    assert not FV.check_denovo_trio(
        trio[0], trio[1], trio[2], allele_index=1)
    assert FV.check_denovo_trio(
        trio[0], trio[1], trio[2], allele_index=2)
    assert FV.check_denovo_trio(
        trio[0], trio[1], trio[2], allele_index=3)
    # assert FV.calc_inheritance_trio(*trio) == Inheritance.denovo


def test_mixed_check_1() -> None:
    # AA,CC -> GG
    trio = [
        np.array([1, 1]),
        np.array([0, 0]),
        np.array([2, 2]),
    ]
    assert not FV.check_denovo_trio(
        trio[0], trio[1], trio[2], allele_index=0)
    assert not FV.check_denovo_trio(
        trio[0], trio[1], trio[2], allele_index=1)
    assert FV.check_denovo_trio(
        trio[0], trio[1], trio[2], allele_index=2)

    assert FV.check_omission_trio(
        trio[0], trio[1], trio[2], allele_index=0)
    assert FV.check_omission_trio(
        trio[0], trio[1], trio[2], allele_index=1)
    assert not FV.check_omission_trio(
        trio[0], trio[1], trio[2], allele_index=2)

    assert not FV.check_mendelian_trio(
        trio[0], trio[1], trio[2], allele_index=0)
    assert not FV.check_mendelian_trio(
        trio[0], trio[1], trio[2], allele_index=1)
    assert not FV.check_mendelian_trio(
        trio[0], trio[1], trio[2], allele_index=2)


def test_mixed_check_2() -> None:
    # AA,CC -> AG
    trio = [
        np.array([1, 1]),
        np.array([0, 0]),
        np.array([2, 1]),
    ]
    assert not FV.check_denovo_trio(
        trio[0], trio[1], trio[2], allele_index=0)
    assert not FV.check_denovo_trio(
        trio[0], trio[1], trio[2], allele_index=1)
    assert FV.check_denovo_trio(
        trio[0], trio[1], trio[2], allele_index=2)

    assert FV.check_omission_trio(
        trio[0], trio[1], trio[2], allele_index=0)
    assert not FV.check_omission_trio(
        trio[0], trio[1], trio[2], allele_index=1)
    assert not FV.check_omission_trio(
        trio[0], trio[1], trio[2], allele_index=2)

    assert not FV.check_mendelian_trio(
        trio[0], trio[1], trio[2], allele_index=0)
    assert FV.check_mendelian_trio(
        trio[0], trio[1], trio[2], allele_index=1)
    assert not FV.check_mendelian_trio(
        trio[0], trio[1], trio[2], allele_index=2)


def test_mixed_check_4() -> None:
    # AA,CC -> AG
    trio = [
        np.array([1, 1]),  # p1
        np.array([0, 0]),  # p2
        np.array([0, 2]),  # ch
    ]
    assert not FV.check_denovo_trio(
        trio[0], trio[1], trio[2], allele_index=0)
    assert not FV.check_denovo_trio(
        trio[0], trio[1], trio[2], allele_index=1)
    assert FV.check_denovo_trio(
        trio[0], trio[1], trio[2], allele_index=2)

    assert not FV.check_omission_trio(
        trio[0], trio[1], trio[2], allele_index=0)
    assert FV.check_omission_trio(
        trio[0], trio[1], trio[2], allele_index=1)
    assert not FV.check_omission_trio(
        trio[0], trio[1], trio[2], allele_index=2)

    assert FV.check_mendelian_trio(
        trio[0], trio[1], trio[2], allele_index=0)
    assert not FV.check_mendelian_trio(
        trio[0], trio[1], trio[2], allele_index=1)
    assert not FV.check_mendelian_trio(
        trio[0], trio[1], trio[2], allele_index=2)


def test_omission_and_denovo() -> None:
    # AA,CC -> AA
    trio = [
        np.array([1, 1]),  # p1
        np.array([1, 1]),  # p2
        np.array([0, 1]),  # ch
    ]

    assert not FV.check_omission_trio(
        trio[0], trio[1], trio[2], allele_index=1)

    assert FV.check_denovo_trio(
        trio[0], trio[1], trio[2], allele_index=0)
