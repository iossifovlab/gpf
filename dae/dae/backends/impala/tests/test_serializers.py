import numpy as np
from dae.backends.impala.serializers import ParquetSerializer


def test_parquet_best_state_serialization(best_state, best_state_serialized):
    serialized = ParquetSerializer.serialize_variant_best_state(best_state)

    assert serialized == best_state_serialized


def test_parquet_best_state_deserialization(best_state, best_state_serialized):
    deserialized = ParquetSerializer.deserialize_variant_best_state(
        best_state_serialized, 4
    )

    assert np.array_equal(deserialized, best_state)


def test_parquet_best_state_serialization_equivalency(best_state):
    serialized = ParquetSerializer.serialize_variant_best_state(best_state)
    deserialized = ParquetSerializer.deserialize_variant_best_state(
        serialized, 4
    )

    assert np.array_equal(deserialized, best_state)
