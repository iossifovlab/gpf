# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines
from collections.abc import Callable

import numpy as np
import pytest

from dae.gpf_instance.gpf_instance import GPFInstance
from dae.pedigrees.family import Family
from dae.utils.variant_utils import best2gt, mat2str
from dae.variants.attributes import GeneticModel
from dae.variants.family_variant import (
    FamilyVariant,
    calculate_simple_best_state,
)
from dae.variants.variant import SummaryAllele, SummaryVariant
from dae.variants_loaders.raw.loader import VariantsGenotypesLoader


@pytest.fixture(scope="session")
def sv1() -> SummaryVariant:
    return SummaryVariant(
        [
            SummaryAllele("1", 11539, "T", None, 0, 0),
            SummaryAllele("1", 11539, "T", "TA", 0, 1),
            SummaryAllele("1", 11539, "T", "TG", 0, 2),
        ],
    )


@pytest.fixture
def fv1(
    fam1: Family,
    sv1: SummaryVariant,
) -> Callable[[np.ndarray | None, np.ndarray | None], FamilyVariant]:

    def build(
        gt: np.ndarray | None,
        best_st: np.ndarray | None,
    ) -> FamilyVariant:
        return FamilyVariant(sv1, fam1, gt, best_st)

    return build


@pytest.mark.parametrize(
    "gt,best_state",
    [
        (np.array([[0, 0, 1], [0, 0, 2]], dtype="int8"), "220/001/001"),
        (np.array([[0, 0, 1], [0, 0, 0]], dtype="int8"), "221/001/000"),
        (np.array([[0, 0, 0], [0, 0, 2]], dtype="int8"), "221/000/001"),
        (np.array([[0, 0, 0], [0, 0, 0]], dtype="int8"), "222/000/000"),
    ],
)
def test_family_variant_simple_best_st(
    fv1: Callable[[np.ndarray | None, np.ndarray | None], FamilyVariant],
    gt: np.ndarray,
    expected: str,
) -> None:
    v = fv1(gt, calculate_simple_best_state(gt, 3))
    print(v)
    print(mat2str(v.best_state))
    assert mat2str(v.best_state) == expected


@pytest.mark.parametrize(
    "gt,best_state",
    [
        (np.array([[-1, 0, 1], [0, 0, 2]], dtype="int8"), "?20/?01/?01"),
        (np.array([[-1, 0, 1], [0, 0, 0]], dtype="int8"), "?21/?01/?00"),
        (np.array([[-1, 0, 0], [0, 0, 2]], dtype="int8"), "?21/?00/?01"),
        (np.array([[-1, 0, 0], [0, 0, 0]], dtype="int8"), "?22/?00/?00"),
    ],
)
def test_family_variant_unknown_simple_best_st(
    fv1: Callable[[np.ndarray | None, np.ndarray | None], FamilyVariant],
    gt: np.ndarray,
    expected: str,
) -> None:
    v = fv1(gt, calculate_simple_best_state(gt, 3))
    assert mat2str(v.best_state) == expected


@pytest.mark.parametrize(
    "gt,expected_best_state",
    [
        (np.array([[0, 0, 1], [0, 0, 2]], dtype="int8"), "220/001/001"),
        (np.array([[0, 0, 1], [0, 0, 0]], dtype="int8"), "221/001/000"),
        (np.array([[0, 0, 0], [0, 0, 2]], dtype="int8"), "221/000/001"),
        (np.array([[0, 0, 0], [0, 0, 0]], dtype="int8"), "222/000/000"),
    ],
)
def test_family_variant_full_best_st(
        fv1: Callable[[np.ndarray | None, np.ndarray | None], FamilyVariant],
        gt: np.ndarray,
        expected: str,
        gpf_instance_2013: GPFInstance,
) -> None:
    v = fv1(gt, None)
    best_state = VariantsGenotypesLoader._calc_best_state(
        v, gpf_instance_2013.reference_genome)
    assert best_state is not None
    assert mat2str(best_state) == expected


@pytest.mark.parametrize(
    "gt,expected_best_state",
    [
        (np.array([[-1, 0, 1], [0, 0, 2]], dtype="int8"), "?20/?01/?01"),
        (np.array([[-1, 0, 1], [0, 0, 0]], dtype="int8"), "?21/?01/?00"),
        (np.array([[-1, 0, 0], [0, 0, 2]], dtype="int8"), "?21/?00/?01"),
        (np.array([[-1, 0, 0], [0, 0, 0]], dtype="int8"), "?22/?00/?00"),
    ],
)
def test_family_variant_unknown_full_best_st(
    fv1: Callable[[np.ndarray | None, np.ndarray | None], FamilyVariant],
    gt: np.ndarray,
    expected: str,
    gpf_instance_2013: GPFInstance,
) -> None:
    v = fv1(gt, None)
    best_state = VariantsGenotypesLoader._calc_best_state(
        v, gpf_instance_2013.reference_genome)
    assert best_state is not None
    assert mat2str(best_state) == expected


@pytest.mark.parametrize(
    "best_state, gt",
    [
        (
            np.array([[2, 2, 1], [0, 0, 1]], dtype="int8"),
            np.array([[0, 0, 1], [0, 0, 0]], dtype="int8"),
        ),
        (
            np.array([[2, 2, 0], [0, 0, 1], [0, 0, 1]], dtype="int8"),
            np.array([[0, 0, 1], [0, 0, 2]], dtype="int8"),
        ),
        (
            np.array([[2, 1, 1], [0, 0, 1]], dtype="int8"),
            np.array([[0, 0, 1], [0, -2, 0]], dtype="int8"),
        ),
    ],
)
def test_best2gt(
    best_state: np.ndarray,
    gt: np.ndarray,
) -> None:
    res = best2gt(best_state)
    print(mat2str(res))

    assert np.all(res == gt)


@pytest.mark.parametrize(
    "best_state, gt, gm",
    [
        (
            np.array([[2, 2, 1], [0, 0, 1]], dtype="int8"),
            np.array([[0, 0, 1], [0, 0, 0]], dtype="int8"),
            GeneticModel.autosomal,
        ),
        (
            np.array([[2, 2, 0], [0, 0, 1], [0, 0, 1]], dtype="int8"),
            np.array([[0, 0, 1], [0, 0, 2]], dtype="int8"),
            GeneticModel.autosomal,
        ),
        (
            np.array([[2, 1, 1], [0, 0, 1]], dtype="int8"),
            np.array([[0, 0, 1], [0, -2, 0]], dtype="int8"),
            GeneticModel.autosomal_broken,
        ),
    ],
)
def test_family_variant_best2gt(
    best_state: np.ndarray,
    gt: np.ndarray,
    gm: GeneticModel,
    fv1: Callable[[np.ndarray | None, np.ndarray | None], FamilyVariant],
    gpf_instance_2013: GPFInstance,
) -> None:
    v = fv1(None, best_state)
    genotype, genetic_model = VariantsGenotypesLoader._calc_genotype(
        v, gpf_instance_2013.reference_genome,
    )
    print(genotype, genetic_model)

    assert np.all(genotype == gt)
    assert genetic_model == gm


@pytest.fixture(scope="session")
def sv_x1() -> SummaryVariant:
    return SummaryVariant(
        [
            SummaryAllele("X", 154931050, "T", None, 0, 0),
            SummaryAllele("X", 154931050, "T", "A", 0, 1),
            SummaryAllele("X", 154931050, "T", "G", 0, 2),
        ],
    )


@pytest.fixture(scope="session")
def sv_x2() -> SummaryVariant:
    return SummaryVariant(
        [
            SummaryAllele("X", 3_000_000, "C", None, 0, 0),
            SummaryAllele("X", 3_000_000, "C", "A", 0, 1),
            SummaryAllele("X", 3_000_000, "C", "A", 0, 2),
        ],
    )


@pytest.fixture
def fv_x1(
    fam1: Family,
    sv_x1: SummaryVariant,
) -> Callable[[np.ndarray | None, np.ndarray | None], FamilyVariant]:
    def build(
        gt: np.ndarray | None,
        best_st: np.ndarray | None,
    ) -> FamilyVariant:
        return FamilyVariant(sv_x1, fam1, gt, best_st)

    return build


@pytest.fixture
def fv_x2(
    fam1: Family,
    sv_x2: SummaryVariant,
) -> Callable[[np.ndarray | None, np.ndarray | None], FamilyVariant]:
    def build(
        gt: np.ndarray | None,
        best_st: np.ndarray | None,
    ) -> FamilyVariant:
        return FamilyVariant(sv_x2, fam1, gt, best_st)

    return build


@pytest.mark.parametrize(
    "best_state, gt, gm1, gm2",
    [
        (
            np.array([[2, 2, 1], [0, 0, 1]], dtype="int8"),
            np.array([[0, 0, 1], [0, 0, 0]], dtype="int8"),
            GeneticModel.pseudo_autosomal,
            GeneticModel.X_broken,
        ),
        (
            np.array([[2, 1, 0], [0, 0, 1]], dtype="int8"),
            np.array([[0, 0, 1], [0, -2, -2]], dtype="int8"),
            GeneticModel.X_broken,
            GeneticModel.X,
        ),
        (
            np.array([[2, 1, 1], [0, 0, 1]], dtype="int8"),
            np.array([[0, 0, 1], [0, -2, 0]], dtype="int8"),
            GeneticModel.X_broken,
            GeneticModel.X_broken,
        ),
    ],
)
def test_family_variant_x_best2gt(
    best_state: np.ndarray,
    gt: np.ndarray,
    gm1: GeneticModel,
    gm2: GeneticModel,
    fv_x1: Callable[[np.ndarray | None, np.ndarray | None], FamilyVariant],
    fv_x2: Callable[[np.ndarray | None, np.ndarray | None], FamilyVariant],
    gpf_instance_2013: GPFInstance,
) -> None:
    genomic_sequence = gpf_instance_2013.reference_genome

    fv1 = fv_x1(None, best_state)
    fv2 = fv_x2(None, best_state)

    genotype, genetic_model = VariantsGenotypesLoader._calc_genotype(
        fv1, genomic_sequence,
    )
    print(genotype, genetic_model)

    assert np.all(genotype == gt)
    assert genetic_model == gm1

    genotype, genetic_model = VariantsGenotypesLoader._calc_genotype(
        fv2, genomic_sequence,
    )
    print(genotype, genetic_model)

    assert np.all(genotype == gt)
    assert genetic_model == gm2


@pytest.mark.parametrize(
    "gt,bs1,gm1,bs2,gm2",
    [
        (
            np.array([[0, 0, 1], [0, 0, 0]], dtype="int8"),
            "221/001/000",
            GeneticModel.pseudo_autosomal,
            "210/001/000",
            GeneticModel.X_broken,
        ),
        (
            np.array([[1, 1, 1], [1, 1, 1]], dtype="int8"),
            "000/222/000",
            GeneticModel.pseudo_autosomal,
            "000/211/000",
            GeneticModel.X_broken,
        ),
        (
            np.array([[0, 1, 0], [1, 2, 1]], dtype="int8"),
            "101/111/010",
            GeneticModel.pseudo_autosomal,
            "100/111/010",
            GeneticModel.X_broken,
        ),
        (
            np.array([[1, 1, 0], [2, 2, 1]], dtype="int8"),
            "001/111/110",
            GeneticModel.pseudo_autosomal,
            "000/111/110",
            GeneticModel.X_broken,
        ),
    ],
)
def test_family_variant_x_gt2best_st(
    fv_x1: Callable[[np.ndarray | None, np.ndarray | None], FamilyVariant],
    fv_x2: Callable[[np.ndarray | None, np.ndarray | None], FamilyVariant],
    gt: np.ndarray,
    bs1: str,
    gm1: GeneticModel,
    bs2: str,
    gm2: GeneticModel,
    gpf_instance_2013: GPFInstance,
) -> None:

    genomic_sequence = gpf_instance_2013.reference_genome

    v = fv_x1(gt, None)
    best_state = VariantsGenotypesLoader._calc_best_state(
        v, genomic_sequence)
    assert best_state is not None
    assert mat2str(best_state) == bs1
    genetic_model = VariantsGenotypesLoader._calc_genetic_model(
        v, genomic_sequence)
    assert genetic_model == gm1

    v = fv_x2(gt, None)
    best_state = VariantsGenotypesLoader._calc_best_state(
        v, genomic_sequence)
    assert best_state is not None
    assert mat2str(best_state) == bs2

    genetic_model = VariantsGenotypesLoader._calc_genetic_model(
        v, genomic_sequence)
    assert genetic_model == gm2
