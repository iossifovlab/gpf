import pytest
from dae.backends.impala.serializers import AlleleParquetSerializer
from dae.backends.dae.loader import DenovoLoader
from dae.pedigrees.loader import FamiliesLoader


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


def test_extra_attributes_serialization_deserialization(
        fixtures_gpf_instance, fixture_dirname):
    families_data = FamiliesLoader.load_simple_families_file(
        fixture_dirname("backends/iossifov_extra_attrs.ped"))

    loader = DenovoLoader(
        families_data, fixture_dirname("backends/iossifov_extra_attrs.tsv"),
        fixtures_gpf_instance.get_genome()
    )

    main_schema = loader.get_attribute("annotation_schema")
    extra_attributes = loader.get_attribute("extra_attributes")

    serializer = AlleleParquetSerializer(main_schema, extra_attributes)
    it = loader.full_variants_iterator()
    variant = next(it)[1][0]
    variant_blob = serializer.serialize_variant(variant)
    extra_blob = serializer.serialize_extra_attributes(variant)
    family = variant.family

    fv = serializer.deserialize_family_variant(
        variant_blob, family, extra_blob)

    assert fv.get_attribute("someAttr")[1] == "asdf"


def test_extra_attributes_impala(extra_attrs_impala):
    variants = extra_attrs_impala.query_variants()
    first_variant = list(variants)[0]
    assert first_variant.get_attribute("someAttr")[1] == "asdf"
