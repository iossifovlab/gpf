import io
import toml
import textwrap
import pytest

from typing import cast, Any, Dict

from dae.genomic_resources.testing import convert_to_tab_separated

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.person_sets import person_set_collections_schema
from dae.pedigrees.loader import FamiliesLoader
from dae.person_sets import PersonSet, PersonSetCollection


@pytest.fixture
def families_fixture():
    ped_content = io.StringIO(convert_to_tab_separated(
        """
            familyId personId dadId	 momId	sex status role
            f1       mom1     0      0      2   1      mom
            f1       dad1     0      0      1   1      dad
            f1       prb1     dad1   mom1   1   2      prb
            f1       sib1     dad1   mom1   2   2      sib
            f1       sib2     dad1   mom1   2   2      sib
            f2       grmom2   0      0      2   1      maternal_grandmother
            f2       grdad2   0      0      1   1      maternal_grandfather
            f2       mom2     grdad2 grmom2 2   1      mom
            f2       dad2     0      0      1   1      dad
            f2       prb2     dad2   mom2   1   2      prb
            f2       sib2_3   dad2   mom2   2   2      sib
        """))
    families = FamiliesLoader(ped_content).load()
    assert families is not None
    return families


def get_person_set_collections_config(content: str):
    return GPFConfigParser.process_config(
        cast(Dict[str, Any], toml.loads(content)),
        {"person_set_collections": person_set_collections_schema},
    ).person_set_collections


@pytest.fixture
def status_person_sets_collection():
    content = textwrap.dedent(
        """
        [person_set_collections]
        selected_person_set_collections = ["status"]
        status.id = "affected_status"
        status.name = "Affected Status"
        status.sources = [{ from = "pedigree", source = "status" }]
        status.domain = [
            {
                id = "affected",
                name = "Affected",
                values = ["affected"],
                color = "#aabbcc"
            },
            {
                id = "unaffected",
                name = "Unaffected",
                values = ["unaffected"],
                color = "#ffffff"
            },
        ]
        status.default = {id = "unknown",name = "Unknown",color = "#aaaaaa"}

        """)

    return get_person_set_collections_config(content)


def test_load_config(status_person_sets_collection):
    assert status_person_sets_collection.status is not None


def test_produce_sets(status_person_sets_collection):
    people_sets = PersonSetCollection._produce_sets(
        status_person_sets_collection.status)
    assert people_sets == {
        "affected": PersonSet(
            "affected", "Affected", {"affected_val"}, "#aabbcc", dict()
        ),
        "unaffected": PersonSet(
            "unaffected", "Unaffected", {"unaffected_val"}, "#ffffff", dict()
        ),
    }


def test_produce_default_person_set(status_person_sets_collection):
    people_set = PersonSetCollection._produce_default_person_set(
        status_person_sets_collection.status)
    assert people_set == PersonSet(
            "unknown", "Unknown", {"DEFAULT"}, "#aaaaaa", dict()
        )


def test_from_pedigree(families_fixture, status_person_sets_collection):
    status_collection = PersonSetCollection.from_families(
        status_person_sets_collection.status, families_fixture
    )

    assert set(status_collection.person_sets.keys()) == \
        {"affected", "unaffected"}

    result_person_ids = set(
        status_collection.person_sets["affected"].persons.keys()
    )
    assert result_person_ids == {
        'prb2', 'sib2_3', 'sib2', 'prb1', 'sib1'
    }


def test_from_pedigree_missing_value_in_domain(families_fixture):

    content = textwrap.dedent(
        """
        [person_set_collections]
        selected_person_set_collections = ["status"]
        status.id = "affected_status"
        status.name = "Affected Status"
        status.sources = [{ from = "pedigree", source = "status" }]
        status.domain = [
            {
                id = "unaffected",
                name = "Unaffected",
                values = ["unaffected"],
                color = "#ffffff"
            },
        ]
        status.default = {id = "unknown",name = "Unknown",color = "#aaaaaa"}

        """)

    config = get_person_set_collections_config(content)

    collection = PersonSetCollection.from_families(
        config.status, families_fixture)

    assert set(collection.person_sets.keys()) == {"unaffected", "unknown"}


def test_from_pedigree_nonexistent_domain(fixture_dirname, families_fixture):
    content = textwrap.dedent("""
        [person_set_collections]
        selected_person_set_collections = ["invalid"]

        invalid.id = "invalid"
        invalid.name = "Nonexisting domain"
        invalid.sources = [
            { from = "pedigree", source = "invalid" },
        ]
        invalid.domain = [
            {id = "sample", name = "sample",
             values = ["sample"], color = "#ffffff"}
        ]

        invalid.default = {id = "unknown", name = "Unknown", color = "#aaaaaa"}
    """)
    config = get_person_set_collections_config(content)

    collection = PersonSetCollection.from_families(
            config.invalid, families_fixture,
        )
    assert set(collection.person_sets.keys()) == {"unknown"}


def test_get_person_color(
        status_person_sets_collection, families_fixture):

    status_collection = PersonSetCollection.from_families(
        status_person_sets_collection.status, families_fixture
    )

    assert (
        PersonSetCollection.get_person_color(
            families_fixture.persons["prb1"], status_collection
        )
        == "#aabbcc"
    )


def test_collection_merging_configs_order(families_fixture):
    role_config = get_person_set_collections_config(textwrap.dedent("""
    [person_set_collections]
    selected_person_set_collections = ["role"]

    role.id = "role"
    role.name = "Role"
    role.sources = [
        { from = "pedigree", source = "role" },
    ]
    role.default = {id = "unknown", name = "Unknown", color="#ffffff"}
    role.domain = [
    {id = "mom", name = "Mother", values = ["mom"], color = "#ffffff"},
    {id = "dad", name = "Father", values = ["dad"], color = "#ffffff"},
    {id = "prb", name = "Proband", values = ["prb"], color = "#ffffff"},
    {id = "sib", name = "Sibling", values = ["sib"], color = "#ffffff"}
    ]
    """))

    role_ext_config = get_person_set_collections_config(textwrap.dedent("""
        [person_set_collections]
        selected_person_set_collections = ["role"]

        role.id = "role"
        role.name = "Role"
        role.sources = [
            { from = "pedigree", source = "role" },
        ]
        role.default = {id = "unknown", name = "Unknown", color="#ffffff"}
        role.domain = [
        {id = "mom", name = "Mother", values = ["mom"], color = "#ffffff"},
        {id = "dad", name = "Father", values = ["dad"], color = "#ffffff"},
        {id = "prb", name = "Proband", values = ["prb"], color = "#ffffff"},
        {id = "sib", name = "Sibling", values = ["sib"], color = "#ffffff"},
        {id = "0_new_role_first", name = "New Role First",
         values = ["maternal_grandmother"], color = "#ffffff"},
        {id = "z_new_role_last", name = "New Role Last",
         values = ["maternal_grandfather"], color = "#ffffff"},
    ]

    """))

    role_collection = PersonSetCollection.from_families(
        role_config.role, families_fixture
    )
    assert len(role_collection.person_sets) == 5

    role_collection_extended = PersonSetCollection.from_families(
        role_ext_config.role, families_fixture
    )
    assert len(role_collection_extended.person_sets) == 6

    merged_config = PersonSetCollection.merge_configs(
        [role_collection, role_collection_extended]
    )

    assert len(merged_config.domain) == 6

    assert [vd.id for vd in merged_config.domain] == [
        "0_new_role_first",
        "dad",
        "mom",
        "prb",
        "sib",
        "z_new_role_last",
    ]


def test_multiple_column_person_set(families_fixture):
    config = get_person_set_collections_config(textwrap.dedent("""
        [person_set_collections]
        selected_person_set_collections = ["status_sex"]

        status_sex.id = "status_sex"
        status_sex.name = "Affected Status and Sex"
        status_sex.sources = [
            { from = "pedigree", source = "status" },
            { from = "pedigree", source = "sex" },
        ]
        status_sex.domain = [
            { id = "affected_male", name = "Affected Male",
            values = ["affected", "M"], color = "#ffffff" },
            { id = "affected_female", name = "Affected Female",
            values = ["affected", "F"], color = "#ffffff" },
            { id = "unaffected_male", name = "Unaffected Male",
            values = ["unaffected", "M"], color = "#ffffff" },
            { id = "unaffected_female", name = "Unaffected Female",
            values = ["unaffected", "F"], color = "#ffffff" },
        ]
        status_sex.default = { id="other", name="Other", color="#aaaaaa"}
    """))

    status_sex_collection = PersonSetCollection.from_families(
        config.status_sex, families_fixture
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
        fixtures_gpf_instance, families_fixture):

    config = get_person_set_collections_config(textwrap.dedent("""
    [person_set_collections]

    pheno_cat.id = "pheno_cat"
    pheno_cat.name = "Phenotype measure categorical"
    pheno_cat.sources = [
        { from = "phenodb", source = "instrument1.categorical" },
    ]
    pheno_cat.domain = [
        {id = "option1", name = "Option 1",
        values = ["option1"], color = "#ffffff"}
        {id = "option2", name = "Option 2",
        values = ["option2"], color = "#aabbcc"},
    ]
    pheno_cat.default = {id = "unknown", name = "Unknown", color="#ffffff"}

    """))

    quads_f1_pheno = fixtures_gpf_instance.get_phenotype_data("quads_f1")
    pheno_categorical_collection = PersonSetCollection.from_families(
        config.pheno_cat, families_fixture, quads_f1_pheno
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
        families_fixture, fixtures_gpf_instance):

    config = get_person_set_collections_config(textwrap.dedent("""
    [person_set_collections]

    pheno_cont.id = "pheno_cont"
    pheno_cont.name = "Phenotype measure continuous"
    pheno_cont.sources = [
        { from = "phenodb", source = "instrument1.continuous" },
    ]
    pheno_cont.domain = [
        {id = "lower", name = "Lower",
         values = ["1", "3"], color = "#ffffff"}
        {id = "higher", name = "Higher",
         values = ["3", "5"], color = "#aabbcc"},
    ]
    pheno_cont.default = {id = "unknown", name = "Unknown", color="#ffffff"}
    """))

    quads_f1_pheno = fixtures_gpf_instance.get_phenotype_data("quads_f1")

    with pytest.raises(AssertionError) as excinfo:
        PersonSetCollection.from_families(
            config.pheno_cont, families_fixture, quads_f1_pheno
        )

    assert "Continuous measures not allowed in person sets! " \
        "(instrument1.continuous)" in str(excinfo.value)


def test_genotype_group_person_sets(fixtures_gpf_instance):
    genotype_data_group = fixtures_gpf_instance.get_genotype_data(
        "person_sets_dataset_1"
    )
    print(genotype_data_group._person_set_collections)

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

    print(phenotype_collection.person_sets)

    unaffected_persons = set(
        phenotype_collection.person_sets["unaffected"].persons.keys()
    )
    assert "phenotype2" not in phenotype_collection.person_sets

    phenotype2_persons = set(
        phenotype_collection.person_sets["phenotype1"].persons.keys()
    )
    assert "person3" not in unaffected_persons
    assert "person3" in phenotype2_persons


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
        and "person4" in phenotype1_persons
    )


@pytest.fixture
def families_fixture2():
    ped_content = io.StringIO(convert_to_tab_separated(
        """
            familyId personId  dadId	momId    sex status role
            ff1      ff1.mom1  0        0        2   1      mom
            ff1      ff1.dad1  0        0        1   1      dad
            ff1      ff1.prb1  ff1.dad1 ff1.mom1 1   2      prb
            ff1      ff1.sib1  ff1.dad1 ff1.mom1 2   2      sib
            ff2      ff2.mom2  0        0        2   1      mom
            ff2      ff2.dad2  0        0        1   1      dad
            ff2      ff2.prb2  ff2.dad2 ff2.mom2 1   2      prb
            ff2      ff2.sib2  ff2.dad2 ff2.mom2 2   2      sib
        """))
    families = FamiliesLoader(ped_content).load()
    assert families is not None
    return families


def test_merge_person_sets(families_fixture, families_fixture2):

    content1 = textwrap.dedent("""
    [person_set_collections]
    selected_person_set_collections = ["phenotype"]
    phenotype.id = "phenotype"
    phenotype.name = "Phenotype"
    phenotype.sources = [{ from = "pedigree", source = "status" }]
    phenotype.domain = [
    {id = "aa",name = "aa",values = ["affected"],color = "1"},
    {id = "unaffected",name = "unaffected",values = ["unaffected"],color = "9"}
    ]
    phenotype.default = {id = "unknown",name = "unknown",color = "#aaaaaa"}
    """)
    config1 = get_person_set_collections_config(content1)
    collection1 = PersonSetCollection.from_families(
        config1.phenotype, families_fixture)
    assert collection1.person_sets is not None, (config1, collection1)

    content2 = textwrap.dedent("""
    [person_set_collections]
    selected_person_set_collections = ["phenotype"]
    phenotype.id = "phenotype"
    phenotype.name = "Phenotype"
    phenotype.sources = [{ from = "pedigree", source = "status" }]
    phenotype.domain = [
    {id = "dd",name = "dd",values = ["affected"],color = "2"},
    {id = "unaffected",name = "unaffected",values = ["unaffected"],color = "9"}
    ]
    phenotype.default = {id = "unknown",name = "unknown",color = "#aaaaaa"}
    """)
    config2 = get_person_set_collections_config(content2)
    collection2 = PersonSetCollection.from_families(
        config2.phenotype, families_fixture2)
    assert collection2.person_sets is not None, (config2, collection2)

    combined_collection = PersonSetCollection.combine(
        [collection1, collection2])

    print(combined_collection)

    assert len(combined_collection) == 3


# # TODO Add unit test for default values in person sets (normal and phenotype)
