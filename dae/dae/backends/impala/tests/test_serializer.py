from dae.backends.impala.serializers import AlleleParquetSerializer
from dae.backends.dae.loader import DenovoLoader
from dae.pedigrees.loader import FamiliesLoader


def test_all_properties_in_blob(vcf_variants_loaders, impala_genotype_storage):
    loader = vcf_variants_loaders("backends/quads_f1")[0]

    fv = list(loader.full_variants_iterator())[0][1][0]
    schema = loader.get_attribute("annotation_schema")
    family = loader.families.get(fv.family_id)
    print(schema)
    schema.create_column("some_score", "float")
    fv.update_attributes({"some_score": [1.24]})

    serializer = AlleleParquetSerializer(schema)
    summary_blobs = serializer.serialize_summary_data(fv.alleles)
    scores_blob = serializer.serialize_scores_data(fv.alleles)
    blob = serializer.serialize_family_variant(
        fv.alleles, summary_blobs, scores_blob)
    deserialized_variant = serializer.deserialize_family_variant(blob, family)
    print("deserialized_variant:", deserialized_variant)
    print(deserialized_variant.alt_alleles[0].attributes)

    print(fv.alt_alleles[0].attributes)

    for prop in schema.names:
        if prop in {"effect_genes", "effect_details"}:
            continue
        if prop == "summary_variant_index":
            continue  # Summary variant index has special handling
        fv_prop = getattr(fv, prop, None)
        if not fv_prop:
            fv_prop = fv.get_attribute(prop)
        deserialized_prop = getattr(deserialized_variant, prop, None)
        if not deserialized_prop:
            deserialized_prop = deserialized_variant.get_attribute(prop)
        if prop == "some_score":
            continue
        print(prop)
        print(fv_prop)
        print(deserialized_prop)
        assert fv_prop == deserialized_prop, prop


def test_extra_attributes_serialization_deserialization(
        fixtures_gpf_instance, fixture_dirname):
    families_data = FamiliesLoader.load_simple_families_file(
        fixture_dirname("backends/iossifov_extra_attrs.ped"))

    loader = DenovoLoader(
        families_data, fixture_dirname("backends/iossifov_extra_attrs.tsv"),
        fixtures_gpf_instance.get_genome().get_genomic_sequence()
    )

    main_schema = loader.get_attribute("annotation_schema")
    extra_attributes = loader.get_attribute("extra_attributes")

    serializer = AlleleParquetSerializer(main_schema, extra_attributes)
    it = loader.full_variants_iterator()
    variant = next(it)[1][0]
    print(variant.gt)
    summary_blobs = serializer.serialize_summary_data(variant.alleles)
    scores_blob = serializer.serialize_scores_data(variant.alleles)
    variant_blob = serializer.serialize_family_variant(
        variant.alleles, summary_blobs, scores_blob
    )
    extra_blob = serializer.serialize_extra_attributes(variant)
    family = variant.family

    fv = serializer.deserialize_family_variant(
        variant_blob, family, extra_blob)

    assert fv.get_attribute("someAttr")[0] == "asdf"


def test_extra_attributes_loading_with_person_id(
        fixtures_gpf_instance, fixture_dirname):
    families_loader = FamiliesLoader(
        fixture_dirname("backends/denovo-db-person-id.ped"))
    families_data = families_loader.load()

    params = {
        "denovo_chrom": "Chr",
        "denovo_pos": "Position",
        "denovo_ref": "Ref",
        "denovo_alt": "Alt",
        "denovo_person_id": "SampleID"
    }

    loader = DenovoLoader(
        families_data, fixture_dirname("backends/denovo-db-person-id.tsv"),
        fixtures_gpf_instance.get_genome().get_genomic_sequence(),
        params=params
    )

    it = loader.full_variants_iterator()
    variants = list(it)
    assert len(variants) == 17
    family_variants = [v[1][0] for v in variants]
    assert family_variants[0].get_attribute("StudyName")[0] == "Turner_2017"
    assert family_variants[1].get_attribute("StudyName")[0] == "Turner_2017"
    assert family_variants[2].get_attribute("StudyName")[0] == "Turner_2017"
    assert family_variants[3].get_attribute("StudyName")[0] == "Lelieveld2016"
    for variant in family_variants:
        print(variant)


def test_extra_attributes_impala(extra_attrs_impala):
    variants = extra_attrs_impala.query_variants()
    first_variant = list(variants)[0]
    assert first_variant.get_attribute("someAttr")[0] == "asdf"


def test_build_allele_batch_dict(
        vcf_variants_loaders, impala_genotype_storage, mocker):
    loader = vcf_variants_loaders("backends/effects_trio")[-1]

    fv = list(loader.full_variants_iterator())[0][1][0]
    schema = loader.get_attribute("annotation_schema")
    family = loader.families.get(fv.family_id)
    assert family is not None

    schema.create_column("some_score", "float")
    fv.update_attributes({"some_score": [1.24]})

    serializer = AlleleParquetSerializer(schema)
    summary_blobs = serializer.serialize_summary_data(fv.alleles)
    scores_blob = serializer.serialize_scores_data(fv.alleles)
    blob = serializer.serialize_family_variant(
        fv.alleles, summary_blobs, scores_blob)
    extra_blob = serializer.serialize_extra_attributes(fv)
    chain = serializer.build_searchable_vectors_summary(fv)
    batch = serializer.build_allele_batch_dict(
        fv.alleles[1], blob, extra_blob, chain)
    print(batch)
