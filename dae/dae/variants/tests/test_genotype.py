"""
Created on Feb 15, 2018

@author: lubo
"""
from dae.utils.regions import Region
import numpy as np


def test_11540_gt(variants_impl):

    fvars = variants_impl("variants_vcf")("backends/a")

    vs = fvars.query_variants(regions=[Region("1", 11539, 11542)])
    v = next(vs)
    assert v.position == 11540

    print(v.gt)
    assert np.all(
        np.array([
            [0, 0, 0, 0, 0, 0, 0, ],
            [0, 0, 2, 0, 0, 0, 0, ]
        ])
        == v.gt
    )

    print(v.best_state)
    assert np.all(
        np.array([
            [2, 2, 1, 2, 2, 2, 2, ],
            [0, 0, 0, 0, 0, 0, 0, ],
            [0, 0, 1, 0, 0, 0, 0, ]])
        == v.best_state
    )

    expected_genotype = [
        [0, 0],
        [0, 0],
        [0, 2],
        [0, 0],
        [0, 0],
        [0, 0],
        [0, 0]]
    assert all([eg == g for (eg, g) in zip(expected_genotype, v.genotype)])

    expected_family_genotype = [
        [0, 0],
        [0, 0],
        [0, 1],
        [0, 0],
        [0, 0],
        [0, 0],
        [0, 0]]
    assert all([
        eg == g
        for (eg, g) in zip(expected_family_genotype, v.family_genotype)])


def test_11540_family_alleles(variants_impl):
    fvars = variants_impl("variants_vcf")("backends/a")

    vs = fvars.query_variants(regions=[Region("1", 11539, 11542)])
    v = next(vs)
    assert v.position == 11540
    assert len(v.alt_alleles) == 1

    aa = v.alt_alleles[0]
    assert aa.allele_index == 2
    assert aa.cshl_variant == "sub(T->A)"

    assert [0, 2] == v.allele_indexes
    assert [0, 1] == v.family_allele_indexes


def test_11548_gt(variants_impl):

    fvars = variants_impl("variants_vcf")("backends/a")

    vs = fvars.query_variants(regions=[Region("1", 11548, 11548)])
    v = next(vs)
    assert v.position == 11548

    print(v.gt)
    assert np.all(
        np.array([
            [2, 2, 2, 2, 2, 2, 2, ],
            [2, 2, 3, 2, 2, 2, 2, ]
        ])
        == v.gt
    )

    print(v.best_state)
    assert np.all(
        np.array([
            [0, 0, 0, 0, 0, 0, 0, ],
            [0, 0, 0, 0, 0, 0, 0, ],
            [2, 2, 1, 2, 2, 2, 2, ],
            [0, 0, 1, 0, 0, 0, 0, ],
            [0, 0, 0, 0, 0, 0, 0, ],
        ])
        == v.best_state
    )

    expected_genotype = [
        [2, 2],
        [2, 2],
        [2, 3],
        [2, 2],
        [2, 2],
        [2, 2],
        [2, 2]]
    assert all([eg == g for (eg, g) in zip(expected_genotype, v.genotype)])

    expected_family_genotype = [
        [1, 1],
        [1, 1],
        [1, 2],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1]]
    assert all([
        eg == g
        for (eg, g) in zip(expected_family_genotype, v.family_genotype)])
