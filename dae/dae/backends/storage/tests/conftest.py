import pytest


@pytest.fixture(scope="session")
def genotype_storage_factory(fixtures_gpf_instance):
    return fixtures_gpf_instance.genotype_storage_db


@pytest.fixture(scope="session")
def filesystem_genotype_storage(genotype_storage_factory):
    return genotype_storage_factory.get_genotype_storage(
        "genotype_filesystem2"
    )


@pytest.fixture(scope="session")
def impala_genotype_storage(genotype_storage_factory):
    return genotype_storage_factory.get_genotype_storage("genotype_impala")


@pytest.fixture(scope="session")
def quads_f1_vcf_config(variants_db_fixture):
    return variants_db_fixture.get_study_config("quads_f1")
