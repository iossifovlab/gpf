# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest


@pytest.fixture(scope="session")
def genotype_storage_factory(fixtures_gpf_instance):
    return fixtures_gpf_instance.genotype_storage_db


@pytest.fixture(scope="session")
def quads_f1_vcf_config(fixtures_gpf_instance):
    return fixtures_gpf_instance.get_genotype_data_config("quads_f1")
