import pytest
import numpy as np
from dae.backends.impala.parquet_io import ParquetSerializer


@pytest.mark.parametrize("gt", [
    np.array([[1, 1, 1], [0, 0, 0]], dtype=np.int8),
    np.array([[2, 1, 1], [1, 0, 0]], dtype=np.int8),
    np.array([[1, 1, 1, 1], [2, 2, 2, 2]], dtype=np.int8),
    np.array([[1, 2, 3, 4], [5, 6, 7, 8]], dtype=np.int8),
])
def test_genotype_serialize_deserialize(gt):
    data = ParquetSerializer.serialize_variant_genotype(gt)
    print("|{}|,|{}|".format(data, bytes(data, 'utf8')))
    gt2 = ParquetSerializer.deserialize_variant_genotype(data)
    print(data)
    print(gt)
    print(gt2)

    assert np.all(gt == gt2)


@pytest.mark.parametrize("alts", [
    ['A', 'C'],
    ['AA', 'CC'],
    ['AA'],
])
def test_alternatives_serialize_deserialize(alts):
    data = ParquetSerializer.serialize_variant_alternatives(alts)
    alts2 = ParquetSerializer.deserialize_variant_alternatives(data)

    assert alts == alts2[1:]


def test_variant_effects_serialize_deserialize(variants_mem):
    fvars = variants_mem("backends/effects_trio")
    vs = list(fvars.query_variants())

    for v in vs:
        data = ParquetSerializer.serialize_variant_effects(v.effects)
        effects2 = ParquetSerializer.deserialize_variant_effects(data)

        assert all([
            e1['effects'] == str(e2)
            for e1, e2 in zip(effects2[1:], v.effects[1:])])
