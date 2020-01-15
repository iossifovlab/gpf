import pytest
import numpy as np
from dae.backends.raw.loader import FamiliesGenotypesDecorator
from dae.variants.attributes import GeneticModel


@pytest.mark.parametrize('vcf,expected', [
    [
        'backends/quads_f1',
        [[True, True]] * 2
    ],
    [
        'backends/quads_f1_X',
        [
            [False, False],
            [True, True],
            [False, False],
            [True, True],
            [False, False]
        ]
    ]
])
def test_get_diploid_males(vcf, expected, variants_vcf):
    fvars = variants_vcf(vcf)
    counter = 0
    for sv, fvs in fvars.full_variants_iterator():
        for fv in fvs:
            assert FamiliesGenotypesDecorator._get_diploid_males(fv) == \
                expected[counter]
            counter += 1


@pytest.mark.parametrize('vcf,expected', [
    [
        'backends/quads_f1',
        [GeneticModel.autosomal] * 2
    ],
    [
        'backends/quads_f1_X',
        [
            GeneticModel.X,
            GeneticModel.pseudo_autosomal,
            GeneticModel.X,
            GeneticModel.pseudo_autosomal,
            GeneticModel.X,
        ]
    ]
])
def test_calc_genetic_model(vcf, expected, variants_vcf, genome_2013):
    fvars = variants_vcf(vcf)
    counter = 0
    for sv, fvs in fvars.full_variants_iterator():
        for fv in fvs:
            genetic_model = FamiliesGenotypesDecorator._calc_genetic_model(
                fv,
                genome_2013
            )
            assert genetic_model == expected[counter]
            counter += 1


@pytest.mark.parametrize('vcf,expected', [
    [
        'backends/quads_f1',
        [
            np.array([
                [1, 2, 1, 2],
                [1, 0, 1, 0],
            ]),
            np.array([
                [2, 1, 1, 2],
                [0, 1, 1, 0],
            ]),
        ]
    ],
    [
        'backends/quads_f1_X',
        [
            np.array([
                [1, 1, 0, 2, 2],
                [1, 0, 1, 0, 0],
            ]),
            np.array([
                [2, 1, 1, 2, 2],
                [0, 1, 1, 0, 0],
            ]),
            np.array([
                [2, 1, 0, 2, 2],
                [0, 0, 1, 0, 0],
            ]),
            np.array([
                [2, 1, 2, 1, 1],
                [0, 1, 0, 1, 1],
            ]),
            np.array([
                [2, 0, 1, 1, 1],
                [0, 1, 0, 1, 1],
            ]),
        ]
    ]
])
def test_calc_best_state(vcf, expected, variants_vcf, genome_2013):
    fvars = variants_vcf(vcf)
    counter = 0
    for sv, fvs in fvars.full_variants_iterator():
        for fv in fvs:
            best_state = FamiliesGenotypesDecorator._calc_best_state(
                fv,
                genome_2013
            )
            assert np.array_equal(best_state, expected[counter])
            counter += 1
