import numpy as np

import pytest
from RegionOperations import Region
from backends.impala.serializers import FamilyVariantSerializer
from backends.impala.parquet_io import VariantsParquetWriter


@pytest.mark.parametrize("fixture_name,pos", [
    ("fixtures/a", 11540),
])
def test_variants_serialize(variants_vcf, fixture_name, pos):

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
    writer.save_variants_to_parquet("test.parquet")
