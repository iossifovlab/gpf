# pylint: disable=W0621,C0114,C0116,W0212,W0613
from collections.abc import Callable
from typing import cast

import pytest
from dae.annotation.annotation_pipeline import AttributeInfo
from dae.configuration.gpf_config_parser import FrozenBox
from dae.gpf_instance.gpf_instance import GPFInstance
from dae.import_tools.cli import run_with_project
from dae.import_tools.import_tools import ImportProject
from dae.pedigrees.loader import FamiliesLoader
from dae.variants.family_variant import FamilyAllele
from dae.variants_loaders.dae.loader import DenovoLoader

from impala_storage.schema1.impala_genotype_storage import ImpalaGenotypeStorage
from impala_storage.schema1.impala_variants import ImpalaVariants
from impala_storage.schema1.serializers import AlleleParquetSerializer


@pytest.fixture(scope="session")
def extra_attrs_impala(
        fixture_dirname: Callable,
        tmp_path_factory: pytest.TempPathFactory,
        gpf_instance_2013: GPFInstance,
        impala_genotype_storage: ImpalaGenotypeStorage) -> ImpalaVariants:
    study_id = f"denovo_extra_attrs_{impala_genotype_storage.storage_id}"
    families_filename = fixture_dirname("backends/iossifov_extra_attrs.ped")
    variants_filename = fixture_dirname("backends/iossifov_extra_attrs.tsv")
    root_path = tmp_path_factory.mktemp(study_id)
    gpf_instance_2013\
        .genotype_storages\
        .register_genotype_storage(impala_genotype_storage)

    project = {
        "id": study_id,
        "input": {
            "pedigree": {
                "file": families_filename,
            },
            "denovo": {
                "files": [
                    variants_filename,
                ],
                "family_id": "familyId",
                "location": "location",
                "variant": "variant",
                "best_state": "bestState",
            },
        },
        "processing_config": {
            "work_dir": str(root_path),
        },
        "destination": {
            "storage_id": impala_genotype_storage.storage_id,
        },
    }
    import_project = ImportProject.build_from_config(
        project, gpf_instance=gpf_instance_2013)
    run_with_project(import_project)

    return impala_genotype_storage.build_backend(
        FrozenBox({"id": study_id}), gpf_instance_2013.reference_genome,
        gpf_instance_2013.gene_models,
    )


def test_all_properties_in_blob(
    vcf_variants_loaders: Callable,
    impala_genotype_storage: ImpalaGenotypeStorage,  # noqa: ARG001
) -> None:
    loader = vcf_variants_loaders("backends/quads_f1")[0]

    fv = next(iter(loader.full_variants_iterator()))[1][0]
    family = loader.families.get(fv.family_id)
    schema: list[AttributeInfo] = []
    print(schema)
    schema.append(AttributeInfo(
        "some_score", "test",
        internal=False,
        parameters={},
        _type="float"))
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

    for attr in schema:
        if attr.name in {"effect_genes", "effect_details"}:
            continue
        if attr.name == "summary_variant_index":
            continue  # Summary variant index has special handling
        fv_prop = getattr(fv, attr.name, None)
        if not fv_prop:
            fv_prop = fv.get_attribute(attr.name)
        deserialized_prop = getattr(deserialized_variant, attr.name, None)
        if not deserialized_prop:
            deserialized_prop = deserialized_variant.get_attribute(attr.name)
        if attr.name == "some_score":
            continue
        print(attr)
        print(fv_prop)
        print(deserialized_prop)
        assert fv_prop == deserialized_prop, attr


def test_extra_attributes_serialization_deserialization(
        fixtures_gpf_instance: GPFInstance, fixture_dirname: Callable) -> None:
    families_data = FamiliesLoader.load_simple_families_file(
        fixture_dirname("backends/iossifov_extra_attrs.ped"))

    loader = DenovoLoader(
        families_data, fixture_dirname("backends/iossifov_extra_attrs.tsv"),
        fixtures_gpf_instance.reference_genome,
        params={
            "denovo_family_id": "familyId",
            "denovo_location": "location",
            "denovo_variant": "variant",
            "denovo_best_state": "bestState",
        },
    )

    main_schema = loader.get_attribute("annotation_schema")
    extra_attributes = loader.get_attribute("extra_attributes")

    serializer = AlleleParquetSerializer(main_schema, extra_attributes)
    full_variants_iterator = loader.full_variants_iterator()
    variant = next(full_variants_iterator)[1][0]
    print(variant.gt)
    summary_blobs = serializer.serialize_summary_data(variant.alleles)
    scores_blob = serializer.serialize_scores_data(variant.alleles)
    variant_blob = serializer.serialize_family_variant(
        cast(list[FamilyAllele], variant.alleles),
        summary_blobs, scores_blob,
    )
    extra_blob = serializer.serialize_extra_attributes(variant)
    family = variant.family

    fv = serializer.deserialize_family_variant(
        variant_blob, family, extra_blob)

    assert fv.get_attribute("someAttr")[0] == "asdf"


def test_extra_attributes_loading_with_person_id(
        fixtures_gpf_instance: GPFInstance, fixture_dirname: Callable) -> None:
    families_loader = FamiliesLoader(
        fixture_dirname("backends/denovo-db-person-id.ped"))
    families_data = families_loader.load()

    params = {
        "denovo_chrom": "Chr",
        "denovo_pos": "Position",
        "denovo_ref": "Ref",
        "denovo_alt": "Alt",
        "denovo_person_id": "SampleID",
    }

    loader = DenovoLoader(
        families_data, fixture_dirname("backends/denovo-db-person-id.tsv"),
        fixtures_gpf_instance.reference_genome,
        params=params,
    )

    full_variants_iterator = loader.full_variants_iterator()
    variants = list(full_variants_iterator)
    assert len(variants) == 17
    family_variants = [v[1][0] for v in variants]
    assert family_variants[0].get_attribute("StudyName")[0] == "Turner_2017"
    assert family_variants[1].get_attribute("StudyName")[0] == "Turner_2017"
    assert family_variants[2].get_attribute("StudyName")[0] == "Turner_2017"
    assert family_variants[3].get_attribute("StudyName")[0] == "Lelieveld2016"
    for variant in family_variants:
        print(variant)


def test_extra_attributes_impala(extra_attrs_impala: ImpalaVariants) -> None:
    variants = extra_attrs_impala.query_variants()
    first_variant = next(iter(variants))
    assert first_variant.get_attribute("someAttr")[0] == "asdf"


def test_build_allele_batch_dict(
    vcf_variants_loaders: Callable,
    impala_genotype_storage: ImpalaGenotypeStorage,  # noqa: ARG001
) -> None:
    loader = vcf_variants_loaders("backends/effects_trio")[-1]

    fv = next(iter(loader.full_variants_iterator()))[1][0]
    family = loader.families.get(fv.family_id)
    assert family, fv.family_id

    schema: list[AttributeInfo] = []
    schema.append(AttributeInfo(
        "some_score", "test",
        internal=False,
        parameters={},
        _type="float"))
    fv.update_attributes({"some_score": [1.24]})

    serializer = AlleleParquetSerializer(schema)
    summary_blobs = serializer.serialize_summary_data(fv.alleles)
    scores_blob = serializer.serialize_scores_data(fv.alleles)
    blob = serializer.serialize_family_variant(
        fv.alleles, summary_blobs, scores_blob)
    extra_blob = serializer.serialize_extra_attributes(fv)
    assert extra_blob is not None
    chain = serializer.build_searchable_vectors_summary(fv)
    batch = serializer.build_allele_batch_dict(
        fv.alleles[1], blob, extra_blob, chain)
    print(batch)
