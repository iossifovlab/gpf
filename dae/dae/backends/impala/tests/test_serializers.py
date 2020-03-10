import pytest
import numpy as np
from dae.backends.impala.serializers import (
    ParquetSerializer,
    AlleleParquetSerializer,
)


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


def test_allele_serialization(variants_vcf):
    fvars = variants_vcf("backends/effects_trio")

    vs = list(fvars.query_variants())
    ser = AlleleParquetSerializer.from_variant(vs[0])

    for nfv in vs:
        print("\n\n")
        print(nfv)
        for allele in nfv.alleles:
            print(allele.attributes)
            serialized = ser.serialize_allele(allele)
            ser.deserialize_allele(serialized)
