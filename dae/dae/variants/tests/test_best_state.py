import numpy as np
import pytest
from dae.variants.family_variant import FamilyAllele
from dae.utils.variant_utils import GENOTYPE_TYPE


@pytest.mark.parametrize(
    'chromosome, position, reference, alternative, ' +
    'allele_index, allele_count, genotype, expected',
    [
        (
            'chr1', 0, 'A', 'T', 1, 2,
            np.array(
                [
                    [0, 0, 0],
                    [0, 0, 1]
                ],
                dtype=GENOTYPE_TYPE
            ),
            np.array(
                [
                    [2, 2, 1],
                    [0, 0, 1]
                ],
                dtype=GENOTYPE_TYPE
            )
        ),
        (
            'chr1', 0, 'A', 'T', 1, 2,
            np.array(
                [
                    [0, 0, 0],
                    [0, 1, 1]
                ],
                dtype=GENOTYPE_TYPE
            ),
            np.array(
                [
                    [2, 1, 1],
                    [0, 1, 1]
                ],
                dtype=GENOTYPE_TYPE
            )
        ),
        (
            'chr1', 0, 'A', 'T', 1, 2,
            np.array(
                [
                    [0, 0, 1],
                    [0, 0, 1]
                ],
                dtype=GENOTYPE_TYPE
            ),
            np.array(
                [
                    [2, 2, 0],
                    [0, 0, 2]
                ],
                dtype=GENOTYPE_TYPE
            )
        ),
        (
            'chr1', 0, 'A', 'G,T', 1, 3,
            np.array(
                [
                    [0, 1, 2],
                    [0, 0, 0]
                ],
                dtype=GENOTYPE_TYPE
            ),
            np.array(
                [
                    [2,  1,  1],
                    [0,  1, 0],
                    [0,  0, 1],
                ],
                dtype=GENOTYPE_TYPE
            )
        ),
        (
            'chr1', 0, 'A', 'G,T', 2, 3,
            np.array(
                [
                    [0, 1, 2],
                    [0, 0, 0]
                ],
                dtype=GENOTYPE_TYPE
            ),
            np.array(
                [
                    [2,  1,  1],
                    [0, 1,  0],
                    [0, 0,  1]
                ],
                dtype=GENOTYPE_TYPE
            )
        ),
    ]
)
def test_allele_best_state(
        chromosome,
        position,
        reference,
        alternative,
        allele_index,
        allele_count,
        genotype,
        expected,
        sample_family):
    fa = FamilyAllele(
        chromosome,
        position,
        reference,
        alternative,
        0,
        allele_index,
        {},
        sample_family,
        genotype,
        None
    )
    fa.update_attributes({'allele_count': allele_count})
    assert np.array_equal(fa.best_st, expected)
