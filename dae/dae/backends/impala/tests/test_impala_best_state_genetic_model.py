import numpy as np

from dae.backends.impala.serializers import ParquetSerializer


def test_best_state_genetic_model(variants_impala, impala_genotype_storage):
    variants_impala("backends/quads_f1")

    impala = impala_genotype_storage.impala_helpers
    db = impala_genotype_storage.storage_config.impala.db

    best_state_expecteds = [
        np.array([[1, 2, 1, 2], [1, 0, 1, 0]], dtype=np.int8),
        np.array([[2, 1, 1, 2], [0, 1, 1, 0]], dtype=np.int8),
    ]

    with impala.connection.cursor() as cursor:
        cursor.execute(
            f"SELECT best_state_data, genetic_model_data "
            f"FROM {db}.quads_f1_variants"
        )
        rows = list(cursor)
        assert np.array(
            [
                ParquetSerializer.deserialize_variant_best_state(row[0], 4)
                == best_state_expecteds[0]
                for row in rows[0:6]
            ]
        ).all()
        assert np.array(
            [
                ParquetSerializer.deserialize_variant_best_state(row[0], 4)
                == best_state_expecteds[1]
                for row in rows[6:13]
            ]
        ).all()

        assert all([isinstance(row[1], int) for row in rows])
        assert all([row[1] == 1 for row in rows])
