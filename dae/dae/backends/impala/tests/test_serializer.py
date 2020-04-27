import pytest
from dae.backends.impala.serializers import AlleleParquetSerializer


@pytest.mark.xfail()
def test_all_properties_in_blob(vcf_variants_loader, impala_genotype_storage):
    loader = vcf_variants_loader("backends/quads_f1")

    fv = list(loader.full_variants_iterator())[0][1][0]
    schema = loader.get_attribute("annotation_schema")
    family = loader.families.get(fv.family_id)
    schema.create_column("some_score", "float")
    fv.update_attributes({"some_score": [1.24]})

    serializer = AlleleParquetSerializer(schema)
    blob = serializer.serialize_variant(fv)
    deserialized_variant = serializer.deserialize_family_variant(blob, family)
    for prop in schema.columns.keys():
        print(prop)
        if prop == "summary_variant_index":
            continue  # Summary variant index has special handling
        fv_prop = getattr(fv, prop, None)
        if not fv_prop:
            fv_prop = fv.get_attribute(prop)
        deserialized_prop = getattr(deserialized_variant, prop, None)
        if not deserialized_prop:
            deserialized_prop = deserialized_variant.get_attribute(prop)

        assert fv_prop == deserialized_prop
