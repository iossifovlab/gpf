import os

from dae.studies.tests.conftest import fixtures_dir
from dae.studies.variants_db import VariantsDb


def test_fixture_variants_db_can_be_loaded(variants_db_fixture):
    assert variants_db_fixture is not None


def test_variants_db_can_create_study_from_config(
    genotype_data_study_configs, variants_db_fixture
):
    test_config = genotype_data_study_configs.get("quads_f1")

    assert (
        variants_db_fixture._make_genotype_study(test_config) is not None
    )


##############################################################


def test_variants_db_studies_simple(
    dae_config_fixture,
    gpf_instance_2013,
    genotype_storage_factory,
):
    assert dae_config_fixture is not None
    assert dae_config_fixture.studies.dir is not None

    assert dae_config_fixture.studies.dir == os.path.join(
        fixtures_dir(), "studies"
    )

    vdb = VariantsDb(
        dae_config_fixture,
        gpf_instance_2013.reference_genome,
        gpf_instance_2013.gene_models,
        genotype_storage_factory,
    )
    assert vdb is not None


def test_variants_db_genotype_data_groups_simple(
    dae_config_fixture,
    gpf_instance_2013,
    genotype_storage_factory,
):
    assert dae_config_fixture is not None
    assert dae_config_fixture.datasets.dir is not None

    assert dae_config_fixture.datasets.dir == os.path.join(
        fixtures_dir(), "datasets"
    )

    vdb = VariantsDb(
        dae_config_fixture,
        gpf_instance_2013.reference_genome,
        gpf_instance_2013.gene_models,
        genotype_storage_factory,
    )
    assert vdb is not None


def test_get_existing_study_config(variants_db_fixture):
    assert variants_db_fixture\
        .get_genotype_study_config("quads_f1") is not None


def test_get_non_existing_study_config(variants_db_fixture):
    assert variants_db_fixture.get_genotype_study_config("ala bala") is None


def test_get_existing_study(variants_db_fixture):
    study = variants_db_fixture.get_genotype_study("inheritance_trio")
    assert study is not None
    vs = study.query_variants()
    vs = list(vs)
    assert len(vs) == 14


def test_query_summary_variants(variants_db_fixture):
    study = variants_db_fixture.get_genotype_study("quads_f1")
    assert study is not None
    vs = study.query_summary_variants()
    vs = list(vs)
    print(vs)

    assert len(vs) == 3


def test_get_non_existing_study(variants_db_fixture):
    study = variants_db_fixture.get_genotype_study("ala bala")
    assert study is None


# def test_get_all_studies(variants_db_fixture):
#     studies = variants_db_fixture.get_all_studies()
#     assert len(studies) == 7


##############################################################


def test_get_all_genotype_group_ids(variants_db_fixture):
    assert set(variants_db_fixture.get_all_genotype_group_ids()) == set(
        [
            "quads_in_parent_ds",
            "composite_dataset_ds",
            "quads_in_child_ds",
            "quads_composite_ds",
            "inheritance_trio_ds",
            "quads_two_families_ds",
            "quads_variant_types_ds",
            "quads_f1_ds",
            "quads_f2_ds",
            "f2_group",
            "Dataset3",
            "f1_group",
            "Dataset2",
            "Dataset1",
            "f3_group",
            "Dataset4",
            "person_sets_dataset_1",
            "person_sets_dataset_2",
            "svmergingdataset",
        ]
    )


def test_get_existing_genotype_data_group_config(variants_db_fixture):
    vdb = variants_db_fixture
    assert (
        vdb.get_genotype_group_config("inheritance_trio_ds") is not None
    )


def test_get_non_existing_genotype_data_group_config(variants_db_fixture):
    assert (
        variants_db_fixture.get_genotype_group_config("ala bala") is None
    )


def test_get_genotype_group(variants_db_fixture):
    genotype_data_group = variants_db_fixture.get_genotype_group(
        "quads_in_parent_ds"
    )
    assert genotype_data_group is not None
    assert genotype_data_group.study_id == "quads_in_parent_ds"


def test_get_existing_genotype_data_group(variants_db_fixture):
    genotype_data_group = variants_db_fixture.get_genotype_group(
        "inheritance_trio_ds"
    )
    assert genotype_data_group is not None
    vs = genotype_data_group.query_variants()
    vs = list(vs)
    assert len(vs) == 14


def test_get_non_existing_genotype_data_group(variants_db_fixture):
    genotype_data_group = variants_db_fixture.get_genotype_group(
        "ala bala"
    )
    assert genotype_data_group is None


def test_get_all_genotype_groups(variants_db_fixture):
    genotype_data_groups = variants_db_fixture.get_all_genotype_groups()
    assert len(genotype_data_groups) == 19


def test_get_all_genotype_group_configs(variants_db_fixture):
    configs = variants_db_fixture.get_all_genotype_group_configs()
    assert len(configs) == 19


##############################################################


def test_get_existing_config(variants_db_fixture):
    vdb = variants_db_fixture
    assert vdb.get_config("inheritance_trio") is not None


def test_get_non_existing_config(variants_db_fixture):
    assert variants_db_fixture.get_config("ala bala") is None


def test_get_existing(variants_db_fixture):
    study = variants_db_fixture.get("inheritance_trio")
    assert study is not None
    vs = study.query_variants()
    vs = list(vs)
    assert len(vs) == 14

    genotype_data_group = variants_db_fixture.get("inheritance_trio_ds")
    assert genotype_data_group is not None
    vs = genotype_data_group.query_variants()
    vs = list(vs)
    assert len(vs) == 14


def test_get_non_existing(variants_db_fixture):
    study = variants_db_fixture.get("ala bala")
    assert study is None


def test_get_all(fixtures_gpf_instance, variants_db_fixture):
    studies = variants_db_fixture.get_all_genotype_data()
    assert len(studies) == 42

    studies = fixtures_gpf_instance.get_all_genotype_data()
    assert len(studies) == 42


def test_get_all_studies_ids(fixtures_gpf_instance, variants_db_fixture):
    fixtures_gpf_instance.reload()

    genotype_ids = fixtures_gpf_instance.get_genotype_data_ids()
    assert len(genotype_ids) == 42, genotype_ids


def test_get_bad_study(fixtures_gpf_instance):
    genotype_data = fixtures_gpf_instance.get_genotype_data("quads_f1_impala")
    assert genotype_data is None
