# pylint: disable=W0621,C0114,C0116,W0212,W0613
import numpy as np

from dae.variants.attributes import GeneticModel


def test_best_state_genetic_model(variants_impala, impala_genotype_storage):
    impala_variants = variants_impala("backends/quads_f1")

    best_state_expecteds = {
        11539: np.array([[1, 2, 1, 2], [1, 0, 1, 0]], dtype=np.int8),
        11540: np.array([[2, 1, 1, 2], [0, 1, 1, 0]], dtype=np.int8),
    }

    variants = list(impala_variants.query_variants())

    for variant in variants:
        assert np.all(
            variant.best_state == best_state_expecteds[variant.position])
    assert all(
        variant.genetic_model == GeneticModel.autosomal
        for variant in variants
    )
