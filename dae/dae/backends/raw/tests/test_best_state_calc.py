"""
Created on Jul 9, 2018

@author: lubo
"""
import pytest

import numpy as np
from dae.variants.attributes import GeneticModel
from dae.variants.family_variant import calculate_simple_best_state
from dae.utils.variant_utils import mat2str, best2gt
from dae.backends.raw.loader import VariantsGenotypesLoader


@pytest.mark.parametrize(
    "gt,bs",
    [
        (np.array([[0, 0, 1], [0, 0, 2]], dtype="int8"), "220/001/001"),
        (np.array([[0, 0, 1], [0, 0, 0]], dtype="int8"), "221/001/000"),
        (np.array([[0, 0, 0], [0, 0, 2]], dtype="int8"), "221/000/001"),
        (np.array([[0, 0, 0], [0, 0, 0]], dtype="int8"), "222/000/000"),
    ],
)
def test_family_variant_simple_best_st(fv1, gt, bs):
    v = fv1(gt, calculate_simple_best_state(gt, 3))
    print(v)
    print(mat2str(v.best_state))
    assert mat2str(v.best_state) == bs


@pytest.mark.parametrize(
    "gt,bs",
    [
        (np.array([[-1, 0, 1], [0, 0, 2]], dtype="int8"), "?20/?01/?01"),
        (np.array([[-1, 0, 1], [0, 0, 0]], dtype="int8"), "?21/?01/?00"),
        (np.array([[-1, 0, 0], [0, 0, 2]], dtype="int8"), "?21/?00/?01"),
        (np.array([[-1, 0, 0], [0, 0, 0]], dtype="int8"), "?22/?00/?00"),
    ],
)
def test_family_variant_unknown_simple_best_st(fv1, gt, bs):
    v = fv1(gt, calculate_simple_best_state(gt, 3))
    print(v)
    print(mat2str(v.best_state))
    assert mat2str(v.best_state) == bs


@pytest.mark.parametrize(
    "gt,bs",
    [
        (np.array([[0, 0, 1], [0, 0, 2]], dtype="int8"), "220/001/001"),
        (np.array([[0, 0, 1], [0, 0, 0]], dtype="int8"), "221/001/000"),
        (np.array([[0, 0, 0], [0, 0, 2]], dtype="int8"), "221/000/001"),
        (np.array([[0, 0, 0], [0, 0, 0]], dtype="int8"), "222/000/000"),
    ],
)
def test_family_variant_full_best_st(fv1, gt, bs, genome_2013):
    v = fv1(gt, None)
    best_state = VariantsGenotypesLoader._calc_best_state(v, genome_2013)
    print(v)
    print(mat2str(best_state))
    assert mat2str(best_state) == bs


@pytest.mark.parametrize(
    "gt,bs",
    [
        (np.array([[-1, 0, 1], [0, 0, 2]], dtype="int8"), "?20/?01/?01"),
        (np.array([[-1, 0, 1], [0, 0, 0]], dtype="int8"), "?21/?01/?00"),
        (np.array([[-1, 0, 0], [0, 0, 2]], dtype="int8"), "?21/?00/?01"),
        (np.array([[-1, 0, 0], [0, 0, 0]], dtype="int8"), "?22/?00/?00"),
    ],
)
def test_family_variant_unknown_full_best_st(fv1, gt, bs, genome_2013):
    v = fv1(gt, None)
    best_state = VariantsGenotypesLoader._calc_best_state(v, genome_2013)
    print(v)
    print(mat2str(best_state))
    assert mat2str(best_state) == bs


@pytest.mark.parametrize(
    "bs, gt",
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
def test_best2gt(bs, gt):
    res = best2gt(bs)
    print(mat2str(res))

    assert np.all(res == gt)


@pytest.mark.parametrize(
    "bs, gt, gm",
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
def test_family_variant_best2gt(bs, gt, gm, fv1, genome_2013):
    v = fv1(None, bs)
    genotype, genetic_model = VariantsGenotypesLoader._calc_genotype(
        v, genome_2013
    )
    print(genotype, genetic_model)

    assert np.all(genotype == gt)
    assert genetic_model == gm


@pytest.mark.parametrize(
    "bs, gt, gm1, gm2",
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
def test_family_variant_X_best2gt(bs, gt, gm1, gm2, fvX1, fvX2, genome_2013):
    genomic_sequence = genome_2013.get_genomic_sequence()

    v1 = fvX1(None, bs)
    v2 = fvX2(None, bs)

    genotype, genetic_model = VariantsGenotypesLoader._calc_genotype(
        v1, genomic_sequence
    )
    print(genotype, genetic_model)

    assert np.all(genotype == gt)
    assert genetic_model == gm1

    genotype, genetic_model = VariantsGenotypesLoader._calc_genotype(
        v2, genomic_sequence
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
def test_family_variant_X_gt2best_st(
        fvX1, fvX2, gt, bs1, gm1, bs2, gm2, genome_2013):

    genomic_sequence = genome_2013.get_genomic_sequence()

    v = fvX1(gt, None)
    best_state = VariantsGenotypesLoader._calc_best_state(
        v, genomic_sequence)
    print(v)
    print(mat2str(best_state))
    assert mat2str(best_state) == bs1
    genetic_model = VariantsGenotypesLoader._calc_genetic_model(
        v, genomic_sequence)
    assert genetic_model == gm1

    v = fvX2(gt, None)
    best_state = VariantsGenotypesLoader._calc_best_state(
        v, genomic_sequence)
    print(v)
    print(mat2str(best_state))
    assert mat2str(best_state) == bs2

    genetic_model = VariantsGenotypesLoader._calc_genetic_model(
        v, genomic_sequence)
    assert genetic_model == gm2
