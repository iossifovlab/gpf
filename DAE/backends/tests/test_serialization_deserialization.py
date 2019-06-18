import numpy as np

import pytest
from RegionOperations import Region
from backends.impala.serializers import FamilyVariantSerializer
from backends.impala.parquet_io import VariantsParquetWriter, ParquetSerializer
from variants.effects import Effect


@pytest.mark.parametrize("fixture_name,pos", [
    ("backends/a", 11540),
])
def test_variants_serialize(test_hdfs, variants_vcf, fixture_name, pos):

    vvars = variants_vcf(fixture_name)
    assert vvars is not None

    vs = vvars.query_variants(
        return_reference=True,
        return_unknown=True,
        regions=[Region("1", pos, pos)])
    vs = list(vs)
    assert len(vs) == 1

    v = vs[0]
    serializer = FamilyVariantSerializer(vvars.families)

    data = serializer.serialize_summary_variant(v)
    assert data is not None
    print(data)

    vv = serializer.deserialize_summary_variant(data)
    assert vv is not None

    assert v.chromosome == vv.chromosome

    data = serializer.serialize_family_variant(v)

    vv = serializer.deserialize_family_variant(data)

    assert vv is not None

    assert v.family_id == vv.family_id
    assert np.all(v.gt == vv.gt)

    buf = serializer.serialize(v)
    print(len(buf))
    vv = serializer.deserialize(buf)

    assert v.family_id == vv.family_id
    assert np.all(v.gt == vv.gt)

    writer = VariantsParquetWriter(vvars.full_variants_iterator())
    writer.save_variants_to_parquet(
        "test.parquet", filesystem=test_hdfs.filesystem())

    assert test_hdfs.exists("test.parquet")


@pytest.mark.parametrize("fixture_name", [
    "backends/effects_trio",
    "backends/a",
    "backends/effects_trio_multi",
    "backends/f1_test",

])
def test_allele_effects_serialization_deserialization(
        variants_vcf, fixture_name):
    fvars = variants_vcf(fixture_name)
    vs = list(fvars.query_variants())
    # assert len(vs) == 10

    for v in vs:
        for aa in v.alt_alleles:
            print(aa.effect)
            data = str(aa.effect)
            effect = Effect.from_string(data)
            assert aa.effect == effect


@pytest.mark.parametrize("fixture_name", [
    "backends/effects_trio",
    "backends/a",
    "backends/effects_trio_multi",
    "backends/f1_test",
    "backends/trios_multi",
    "backends/trios2",
])
def test_variant_effects_serialization_deserialization(
        variants_vcf, fixture_name):
    fvars = variants_vcf(fixture_name)
    vs = list(fvars.query_variants())
    # assert len(vs) == 10

    for v in vs:
        print(v.effects)

        data = ParquetSerializer.serialize_variant_effects(v.effects)
        effects = ParquetSerializer.deserialize_variant_effects(data)
        assert all(e1 == e2 for e1, e2 in zip(effects, v.effects))
