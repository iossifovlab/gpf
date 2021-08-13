import os
import pytest


def fixtures_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures"))


def studies_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), "fixtures/studies")
    )


def genotype_data_groups_dir():
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), "fixtures/datasets")
    )


@pytest.fixture(scope="session")
def local_gpf_instance(gpf_instance):
    gpf_instance = gpf_instance(fixtures_dir())
    return gpf_instance


# @pytest.fixture(scope="session")
# def vdb_fixture(local_gpf_instance):
#     return local_gpf_instance._variants_db


@pytest.fixture(scope="session")
def study1(local_gpf_instance):
    return local_gpf_instance.get_genotype_data("Study1")


@pytest.fixture(scope="session")
def study2(local_gpf_instance):
    return local_gpf_instance.get_genotype_data("Study2")


@pytest.fixture(scope="session")
def study4(local_gpf_instance):
    return local_gpf_instance.get_genotype_data("Study4")


@pytest.fixture(scope="session")
def genotype_data_group1(local_gpf_instance):
    return local_gpf_instance.get_genotype_data("Dataset1")


# @pytest.fixture(scope="session")
# def study1_config(local_gpf_instance):
#     return local_gpf_instance.get_genotype_data_config("Study1")


# @pytest.fixture(scope="session")
# def genotype_data_group2_config(local_gpf_instance):
#     return local_gpf_instance.get_genotype_data_config("Dataset2")


# @pytest.fixture(scope="session")
# def genotype_data_group3_config(local_gpf_instance):
#     return local_gpf_instance.get_genotype_data_config("Dataset3")


# @pytest.fixture(scope="session")
# def genotype_data_group4_config(local_gpf_instance):
#     return local_gpf_instance.get_genotype_data_config("Dataset4")


@pytest.fixture(scope="session")
def families_list(study1):
    return [
        study1.families["f4"],
        study1.families["f5"],
        study1.families["f7"],
        study1.families["f8"],
    ]


@pytest.fixture(scope="session")
def denovo_variants_st1(study1):
    denovo_variants = study1.query_variants(limit=None, inheritance="denovo",)
    denovo_variants = list(denovo_variants)

    assert len(denovo_variants) == 3
    return denovo_variants


@pytest.fixture(scope="session")
def denovo_variants_ds1(genotype_data_group1):
    denovo_variants = genotype_data_group1.query_variants(
        limit=None, inheritance="denovo",
    )
    denovo_variants = list(denovo_variants)

    assert len(denovo_variants) == 8
    return denovo_variants


@pytest.fixture(scope="session")
def remove_common_reports(common_report_facade):
    all_configs = common_report_facade.get_all_common_report_configs()
    temp_files = [config.file_path for config in all_configs]

    for temp_file in temp_files:
        print(f"removing common report: {temp_file}")
        if os.path.exists(temp_file):
            os.remove(temp_file)

    yield

    for temp_file in temp_files:
        print(f"removing common report: {temp_file}")
        if os.path.exists(temp_file):
            os.remove(temp_file)


@pytest.fixture
def phenotype_role_collection(study1):
    return study1.get_person_set_collection("phenotype")


@pytest.fixture
def phenotype_role_sets(phenotype_role_collection):
    person_sets = []
    for person_set in phenotype_role_collection.person_sets.values():
        if len(person_set.persons) > 0:
            person_sets.append(person_set)
    return person_sets
