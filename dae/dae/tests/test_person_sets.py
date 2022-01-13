import pytest

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.person_sets import person_set_collections_schema
from dae.pedigrees.loader import FamiliesLoader
from dae.person_sets import PersonSet, PersonSetCollection


def get_person_set_collections_config(config_path):
    return GPFConfigParser.load_config(
        config_path, {"person_set_collections": person_set_collections_schema},
    ).person_set_collections


def test_load_config(fixture_dirname):
    config = get_person_set_collections_config(
        fixture_dirname("sample_person_sets.toml")
    )
    assert hasattr(config, "status") and hasattr(config, "phenotype")


def test_produce_sets(fixture_dirname):
    config = get_person_set_collections_config(
        fixture_dirname("sample_person_sets.toml")
    )
    people_sets = PersonSetCollection._produce_sets(config.status)
    assert people_sets == {
        "affected": PersonSet(
            "affected", "Affected", {"affected_val"}, "#aabbcc", dict()
        ),
        "unaffected": PersonSet(
            "unaffected", "Unaffected", {"unaffected_val"}, "#ffffff", dict()
        ),
        "unknown": PersonSet(
            "unknown", "Unknown", {"DEFAULT"}, "#aaaaaa", dict()
        ),
    }


def test_from_pedigree(fixture_dirname):
    config = get_person_set_collections_config(
        fixture_dirname("quads_f1_person_sets.toml")
    )
    quads_f1_families = FamiliesLoader(
        fixture_dirname("studies/quads_f1/data/quads_f1.ped")
    ).load()
    status_collection = PersonSetCollection.from_families(
        config.status, quads_f1_families
    )

    result_person_ids = set(
        status_collection.person_sets["affected"].persons.keys()
    )
    assert result_person_ids == {
        'prb2', 'sib2_3', 'sib2', 'prb1', 'sib1'
    }


def test_from_pedigree_missing_value_in_domain(fixture_dirname):
    config = get_person_set_collections_config(
        fixture_dirname("quads_f1_person_sets_incomplete_domain.toml")
    )
    quads_f1_families = FamiliesLoader(
        fixture_dirname("studies/quads_f1/data/quads_f1.ped")
    ).load()

    with pytest.raises(AssertionError) as excinfo:
        PersonSetCollection.from_families(
            config.status, quads_f1_families,
        )
    assert "Domain for 'status' does not have the value " \
        "'frozenset({'affected'})'!" in str(excinfo.value)


def test_from_pedigree_nonexistent_domain(fixture_dirname):
    config = get_person_set_collections_config(
        fixture_dirname("quads_f1_person_sets_nonexistent_domain.toml")
    )
    quads_f1_families = FamiliesLoader(
        fixture_dirname("studies/quads_f1/data/quads_f1.ped")
    ).load()

    with pytest.raises(AssertionError) as excinfo:
        PersonSetCollection.from_families(
            config.invalid, quads_f1_families,
        )

    assert "Domain for 'invalid' does not have the value " \
        "'frozenset({None})'!" in str(excinfo.value)


def test_get_person_color(fixture_dirname):
    config = get_person_set_collections_config(
        fixture_dirname("quads_f1_person_sets.toml")
    )
    quads_f1_families = FamiliesLoader(
        fixture_dirname("studies/quads_f1/data/quads_f1.ped")
    ).load()
    status_collection = PersonSetCollection.from_families(
        config.status, quads_f1_families
    )

    assert (
        PersonSetCollection.get_person_color(
            quads_f1_families.persons["prb1"], status_collection
        )
        == "#aabbcc"
    )


def test_genotype_group_person_sets(fixtures_gpf_instance):
    genotype_data_group = fixtures_gpf_instance.get_genotype_data(
        "person_sets_dataset_1"
    )

    phenotype_collection = genotype_data_group.get_person_set_collection(
        "phenotype"
    )

    expected_unaffected_persons = set(
        ["person1", "person2", "person5", "person6"]
    )
    assert (
        set(phenotype_collection.person_sets["unaffected"].persons.keys())
        == expected_unaffected_persons
    )


def test_genotype_group_person_sets_overlapping(fixtures_gpf_instance):
    genotype_data_group = fixtures_gpf_instance.get_genotype_data(
        "person_sets_dataset_2"
    )

    phenotype_collection = genotype_data_group.get_person_set_collection(
        "phenotype"
    )

    unaffected_persons = set(
        phenotype_collection.person_sets["unaffected"].persons.keys()
    )
    phenotype1_persons = set(
        phenotype_collection.person_sets["phenotype1"].persons.keys()
    )
    assert "person3" in unaffected_persons and "person3" in phenotype1_persons


def test_genotype_group_person_sets_subset(fixtures_gpf_instance):
    genotype_data_group_config = fixtures_gpf_instance.\
        get_genotype_data_config("person_sets_dataset_1")
    genotype_data_group = \
        fixtures_gpf_instance._variants_db._load_genotype_group(
            genotype_data_group_config)

    # Remove a person to simulate a subset of people being used
    del genotype_data_group.families.persons["person4"]
    genotype_data_group._person_set_collections = dict()
    genotype_data_group._build_person_set_collections()

    phenotype_collection = genotype_data_group.get_person_set_collection(
        "phenotype"
    )

    unaffected_persons = set(
        phenotype_collection.person_sets["unaffected"].persons.keys()
    )
    phenotype1_persons = set(
        phenotype_collection.person_sets["phenotype1"].persons.keys()
    )
    assert (
        "person4" not in unaffected_persons
        and "person4" not in phenotype1_persons
    )


def test_collection_merging_ordering(fixture_dirname):
    config = get_person_set_collections_config(
        fixture_dirname("quads_f1_person_sets.toml")
    )
    config_ext = get_person_set_collections_config(
        fixture_dirname("quads_f1_person_sets_extended_roles.toml")
    )

    filename = fixture_dirname("studies/quads_f1/data/quads_f1.ped")
    print(filename)

    quads_f1_families = FamiliesLoader(
        fixture_dirname("studies/quads_f1/data/quads_f1.ped")
    ).load()

    role_collection = PersonSetCollection.from_families(
        config.role, quads_f1_families
    )
    role_collection_extended = PersonSetCollection.from_families(
        config_ext.role, quads_f1_families
    )

    merged_role_collections = PersonSetCollection.merge(
        [role_collection, role_collection_extended],
        quads_f1_families,
        "role",
        "Merged Roles Collection"
    )

    assert list(merged_role_collections.person_sets.keys()) == [
        "0_new_role_first",
        "dad",
        "mom",
        "prb",
        "sib",
        "unknown",
        "z_new_role_last",
    ]


def test_multiple_column_person_set(fixture_dirname):
    config = get_person_set_collections_config(
        fixture_dirname("quads_f1_person_sets_multiple_columns.toml")
    )
    quads_f1_families = FamiliesLoader(
        fixture_dirname("studies/quads_f1/data/quads_f1.ped")
    ).load()
    status_sex_collection = PersonSetCollection.from_families(
        config.status_sex, quads_f1_families
    )

    affected_male = set(
        status_sex_collection.person_sets["affected_male"].persons.keys()
    )

    affected_female = set(
        status_sex_collection.person_sets["affected_female"].persons.keys()
    )

    assert affected_male == {'prb1', 'prb2'}
    assert affected_female == {'sib1', 'sib2', 'sib2_3'}


def test_phenotype_person_set_categorical(
    fixture_dirname, fixtures_gpf_instance
):
    config = get_person_set_collections_config(
        fixture_dirname("quads_f1_person_sets_phenotype.toml")
    )
    quads_f1_families = FamiliesLoader(
        fixture_dirname("studies/quads_f1/data/quads_f1.ped")
    ).load()
    quads_f1_pheno = fixtures_gpf_instance.get_phenotype_data("quads_f1")
    pheno_categorical_collection = PersonSetCollection.from_families(
        config.pheno_cat, quads_f1_families, quads_f1_pheno
    )

    option1 = set(
        pheno_categorical_collection.person_sets["option1"].persons.keys()
    )

    option2 = set(
        pheno_categorical_collection.person_sets["option2"].persons.keys()
    )

    assert option1 == {"mom1"}
    assert option2 == {"prb1"}


def test_phenotype_person_set_continuous(
    fixture_dirname, fixtures_gpf_instance
):
    config = get_person_set_collections_config(
        fixture_dirname("quads_f1_person_sets_phenotype.toml")
    )
    quads_f1_families = FamiliesLoader(
        fixture_dirname("studies/quads_f1/data/quads_f1.ped")
    ).load()
    quads_f1_pheno = fixtures_gpf_instance.get_phenotype_data("quads_f1")

    with pytest.raises(AssertionError) as excinfo:
        PersonSetCollection.from_families(
            config.pheno_cont, quads_f1_families, quads_f1_pheno
        )

    assert "Continuous measures not allowed in person sets! " \
        "(instrument1.continuous)" in str(excinfo.value)

# TODO Add unit test for default values in person sets (normal and phenotype)
