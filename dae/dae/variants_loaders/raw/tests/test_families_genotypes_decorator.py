# pylint: disable=W0621,C0114,C0116,W0212,W0613,too-many-lines

import pytest
import numpy as np
from dae.pedigrees.loader import FamiliesLoader

from dae.variants_loaders.raw.loader import VariantsGenotypesLoader
from dae.variants_loaders.dae.loader import DenovoLoader
from dae.variants.attributes import GeneticModel


@pytest.mark.parametrize(
    "vcf,expected",
    [
        ["backends/quads_f1", [[True, True]] * 2],
        [
            "backends/quads_f1_X",
            [
                [False, False],
                [True, True],
                [False, False],
                [True, True],
                [False, False],
            ],
        ],
    ],
)
def test_get_diploid_males(vcf, expected, vcf_variants_loaders):
    loaders = vcf_variants_loaders(vcf)
    loader = loaders[0]
    assert loader is not None

    counter = 0
    for _sv, fvs in loader.full_variants_iterator():
        for fv in fvs:
            assert (
                VariantsGenotypesLoader._get_diploid_males(fv)
                == expected[counter]
            )
            counter += 1


@pytest.mark.parametrize(
    "vcf,expected",
    [
        ["backends/quads_f1", [GeneticModel.autosomal] * 2],
        [
            "backends/quads_f1_X",
            [
                GeneticModel.X,
                GeneticModel.pseudo_autosomal,
                GeneticModel.X,
                GeneticModel.pseudo_autosomal,
                GeneticModel.X,
            ],
        ],
    ],
)
def test_vcf_loader_genetic_model(
        vcf, expected, vcf_variants_loaders):

    loaders = vcf_variants_loaders(vcf)
    loader = loaders[0]
    assert loader is not None

    counter = 0
    for _sv, fvs in loader.full_variants_iterator():
        for fv in fvs:
            assert fv._genetic_model is not None
            for fa in fv.alleles:
                assert fa._genetic_model is not None

            assert fv.genetic_model == expected[counter], (
                fv.genetic_model, expected[counter], counter, fv)
            for fa in fv.alleles:
                assert fa._genetic_model == expected[counter]
            counter += 1


@pytest.mark.parametrize(
    "vcf,expected",
    [
        [
            "backends/quads_f1",
            [
                np.array([[1, 2, 1, 2], [1, 0, 1, 0]]),
                np.array([[2, 1, 1, 2], [0, 1, 1, 0]]),
            ],
        ],
        [
            "backends/quads_f1_X",
            [
                np.array([[1, 1, 0, 2, 2], [1, 0, 1, 0, 0]]),
                np.array([[2, 1, 1, 2, 2], [0, 1, 1, 0, 0]]),
                np.array([[2, 1, 0, 2, 2], [0, 0, 1, 0, 0]]),
                np.array([[2, 1, 2, 1, 1], [0, 1, 0, 1, 1]]),
                np.array([[2, 0, 1, 1, 1], [0, 1, 0, 1, 1]]),
            ],
        ],
    ],
)
def test_vcf_loader_best_state(
        vcf, expected, vcf_variants_loaders):

    loaders = vcf_variants_loaders(vcf)
    loader = loaders[0]
    assert loader is not None

    counter = 0
    for _sv, fvs in loader.full_variants_iterator():
        for fv in fvs:
            assert fv._best_state is not None
            for fa in fv.alleles:
                assert fa._best_state is not None

            assert np.array_equal(fv.best_state, expected[counter]), counter
            for fa in fv.alleles:
                assert np.array_equal(fa.best_state, expected[counter])

            counter += 1


def test_families_genotypes_decorator_broken_x(
        fixture_dirname, gpf_instance_2013):

    families_loader = FamiliesLoader(
        fixture_dirname("backends/denovo_families.txt"),
        **{"ped_file_format": "simple"},
    )
    families = families_loader.load()

    variants_loader = DenovoLoader(
        families, fixture_dirname("backends/denovo_X_broken.txt"),
        gpf_instance_2013.reference_genome
    )

    for _sv, fvs in variants_loader.full_variants_iterator():
        for fv in fvs:
            print(fv, fv.genetic_model)
            assert fv.genetic_model == GeneticModel.X_broken
