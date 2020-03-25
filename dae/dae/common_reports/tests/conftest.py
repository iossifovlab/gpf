import pytest

import os

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.pedigrees.families_groups import FamiliesGroups
from dae.person_sets import PersonSetCollection

from dae.common_reports.people_filters import (
    PeopleGroupFilter,
    MultiFilter,
    FilterCollection,
)


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


@pytest.fixture(scope="session")
def vdb_fixture(local_gpf_instance):
    return local_gpf_instance._variants_db


@pytest.fixture(scope="session")
def common_report_facade(local_gpf_instance):
    return local_gpf_instance._common_report_facade


@pytest.fixture(scope="session")
def study1(vdb_fixture):
    return vdb_fixture.get_study_wdae_wrapper("Study1")


@pytest.fixture(scope="session")
def study2(vdb_fixture):
    return vdb_fixture.get_study_wdae_wrapper("Study2")


@pytest.fixture(scope="session")
def study4(vdb_fixture):
    return vdb_fixture.get_study_wdae_wrapper("Study4")


@pytest.fixture(scope="session")
def genotype_data_group1(vdb_fixture):
    return vdb_fixture.get_genotype_data_group_wdae_wrapper("Dataset1")


@pytest.fixture(scope="session")
def study1_config(vdb_fixture):
    return vdb_fixture.get_study_config("Study1")


@pytest.fixture(scope="session")
def genotype_data_group2_config(vdb_fixture):
    return vdb_fixture.get_genotype_data_group_config("Dataset2")


@pytest.fixture(scope="session")
def genotype_data_group3_config(vdb_fixture):
    return vdb_fixture.get_genotype_data_group_config("Dataset3")


@pytest.fixture(scope="session")
def genotype_data_group4_config(vdb_fixture):
    return vdb_fixture.get_genotype_data_group_config("Dataset4")


@pytest.fixture(scope="session")
def groups():
    return [
        GPFConfigParser._dict_to_namedtuple(
            {
                "name": "Role and Diagnosis",
                "people_group_ids": ["role", "phenotype"],
            }
        )
    ]


@pytest.fixture(scope="session")
def selected_people_groups():
    return ["phenotype"]


@pytest.fixture(scope="session")
def people_groups(study1_config):
    return study1_config.people_group


@pytest.fixture(scope="session")
def families_groups(people_groups):
    def builder(study):
        families_groups = FamiliesGroups.from_config(
            study.families, people_groups
        )
        families_groups.add_predefined_groups(
            ["status", "sex", "role", "role.sex", "family_size"]
        )
        return families_groups

    return builder


@pytest.fixture(scope="session")
def filter_role(study1, families_groups):
    fg = families_groups(study1)
    return PeopleGroupFilter(fg["role"], "mom", name="Mother")


@pytest.fixture(scope="session")
def filter_people_group(study1, families_groups):
    fg = families_groups(study1)
    return PeopleGroupFilter(fg["phenotype"], "pheno", name="Pheno")


@pytest.fixture(scope="function")
def filter_object(filter_role):
    return MultiFilter([filter_role])


@pytest.fixture(scope="function")
def filter_objects(study1, families_groups, groups):
    return FilterCollection.build_filter_objects(
        families_groups(study1), groups
    )


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
def common_reports_config(common_report_facade):
    return common_report_facade.get_common_report_config("Study1")


@pytest.fixture(scope="session")
def generate_common_reports(common_report_facade):
    common_report_facade.generate_all_common_reports()


@pytest.fixture(scope="session")
def remove_common_reports(common_report_facade):
    all_configs = common_report_facade.get_all_common_report_configs()
    temp_files = [config.file_path for config in all_configs]

    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)

    yield

    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)


@pytest.fixture
def phenotype_role_collection(study1):
    return PersonSetCollection.compose(
        study1.get_person_set_collection("phenotype"),
        study1.get_person_set_collection("role"),
        name="Role and Diagnosis",
    )
