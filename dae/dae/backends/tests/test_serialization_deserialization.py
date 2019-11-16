import pytest
from dae.backends.impala.serializers import ParquetSerializer
from dae.variants.effects import Effect


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
        assert all([
            e1['effects'] == str(e2)
            for e1, e2 in zip(effects[1:], v.effects[1:])
        ])
