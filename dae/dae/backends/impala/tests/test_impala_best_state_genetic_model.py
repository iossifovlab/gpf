# pylint: disable=W0621,C0114,C0116,W0212,W0613
import numpy as np

from dae.variants.attributes import GeneticModel
from dae.backends.impala.serializers import AlleleParquetSerializer


def test_best_state_genetic_model(variants_impala, impala_genotype_storage):
    impala_variants = variants_impala("backends/quads_f1")
    families = impala_variants.families

    impala = impala_genotype_storage.impala_helpers
    db = impala_genotype_storage.storage_config.impala.db

    best_state_expecteds = [
        np.array([[1, 2, 1, 2], [1, 0, 1, 0]], dtype=np.int8),
        np.array([[2, 1, 1, 2], [0, 1, 1, 0]], dtype=np.int8),
    ]

    with impala.connection().cursor() as cursor:
        cursor.execute(
            f"SELECT variant_data, family_id FROM {db}.quads_f1_variants")
        rows = list(cursor)
        serializer = AlleleParquetSerializer(None)
        variants = []

        for row in rows:
            family = families[row[1]]
            v = serializer.deserialize_family_variant(row[0], family)
            print(v)

            variants.append(v)

        assert np.array(
            [
                variant.best_state == best_state_expecteds[0]
                for variant in variants[0:6]
            ]
        ).all()
        assert np.array(
            [
                variant.best_state == best_state_expecteds[1]
                for variant in variants[6:13]
            ]
        ).all()

        assert all(
            variant.genetic_model == GeneticModel.autosomal
            for variant in variants
        )
