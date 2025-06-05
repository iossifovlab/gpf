# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pathlib
import textwrap
from unittest.mock import patch

import pytest
import toml

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.person_sets import person_set_collections_schema
from dae.gpf_instance import GPFInstance
from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.loader import FamiliesLoader
from dae.person_sets import (
    PersonSet,
    PersonSetCollection,
    PersonSetCollectionConfig,
    parse_person_set_collections_study_config,
)
from dae.testing import setup_pedigree


def get_person_set_collections_config(
    content: str,
) -> dict[str, PersonSetCollectionConfig]:
    config = GPFConfigParser.process_config(
        toml.loads(content),
        {"person_set_collections": person_set_collections_schema},
    )
    return parse_person_set_collections_study_config(config)


@pytest.fixture
def status_person_sets_collection() -> dict[str, PersonSetCollectionConfig]:
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


def test_load_config(
    status_person_sets_collection: dict[str, PersonSetCollectionConfig],
) -> None:
    assert status_person_sets_collection["status"] is not None


def test_produce_sets(
    status_person_sets_collection: dict[str, PersonSetCollectionConfig],
) -> None:
    people_sets = PersonSetCollection._produce_sets(
        status_person_sets_collection["status"])
    assert people_sets == {
        "affected": PersonSet(
            "affected", "Affected", ("affected_val", ), "#aabbcc", {},
        ),
        "unaffected": PersonSet(
            "unaffected", "Unaffected", ("unaffected_val", ), "#ffffff", {},
        ),
    }


def test_produce_default_person_set(
    status_person_sets_collection: dict[str, PersonSetCollectionConfig],
) -> None:
    people_set = PersonSetCollection._produce_default_person_set(
        status_person_sets_collection["status"])
    assert people_set == PersonSet(
        "unknown", "Unknown", (), "#aaaaaa", {})


def test_from_pedigree(
    families_fixture: FamiliesData,
    status_person_sets_collection: dict[str, PersonSetCollectionConfig],
) -> None:
    status_collection = PersonSetCollection.from_families(
        status_person_sets_collection["status"], families_fixture,
    )

    assert set(status_collection.person_sets.keys()) == \
        {"affected", "unaffected", "unknown"}

    result_person_ids = set(
        status_collection.person_sets["affected"].persons.keys(),
    )

    assert result_person_ids == {
        ("f2", "prb2"), ("f2", "sib2_3"),
        ("f1", "sib2"), ("f1", "prb1"), ("f1", "sib1"),
    }


def test_from_pedigree_missing_value_in_domain(
    families_fixture: FamiliesData,
) -> None:

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
    status_config = config["status"]
    collection = PersonSetCollection.from_families(
        status_config, families_fixture)

    assert set(collection.person_sets.keys()) == {"unaffected", "unknown"}


def test_from_pedigree_nonexistent_domain(
    families_fixture: FamiliesData,
) -> None:
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
        config["invalid"], families_fixture)
    assert set(collection.person_sets.keys()) == {"unknown"}


def test_get_person_color(
    status_person_sets_collection: dict[str, PersonSetCollectionConfig],
    families_fixture: FamiliesData,
) -> None:

    status_collection = PersonSetCollection.from_families(
        status_person_sets_collection["status"], families_fixture,
    )

    assert (
        PersonSetCollection.get_person_color(
            families_fixture.persons["f1", "prb1"], status_collection,
        )
        == "#aabbcc"
    )


def test_collection_merging_configs_order(
    families_fixture: FamiliesData,
) -> None:
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
        role_config["role"], families_fixture,
    )
    assert len(role_collection.person_sets) == 5

    role_collection_extended = PersonSetCollection.from_families(
        role_ext_config["role"], families_fixture,
    )
    assert len(role_collection_extended.person_sets) == 6

    merged_config = PersonSetCollection.merge_configs(
        [role_collection, role_collection_extended],
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


def test_multiple_column_person_set(
    families_fixture: FamiliesData,
) -> None:
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
        config["status_sex"], families_fixture,
    )

    affected_male = set(
        status_sex_collection.person_sets["affected_male"].persons.keys(),
    )

    affected_female = set(
        status_sex_collection.person_sets["affected_female"].persons.keys(),
    )

    assert affected_male == {("f1", "prb1"), ("f2", "prb2")}
    assert affected_female == {
        ("f1", "sib1"), ("f1", "sib2"), ("f2", "sib2_3")}


def test_phenotype_person_set_categorical(
    t4c8_instance: GPFInstance,
    families_fixture: FamiliesData,
) -> None:

    config = get_person_set_collections_config(textwrap.dedent("""
    [person_set_collections]
    selected_person_set_collections = ["pheno_cat"]
    pheno_cat.id = "pheno_cat"
    pheno_cat.name = "Phenotype measure categorical"
    pheno_cat.sources = [
        { from = "phenodb", source = "i1.m5" },
    ]
    pheno_cat.domain = [
        {id = "val3", name = "Value 3",
        values = ["val3"], color = "#aabbcc"},
        {id = "val4", name = "Value 4",
        values = ["val4"], color = "#aabbcc"},
    ]
    pheno_cat.default = {id = "unknown", name = "Unknown", color="#ffffff"}

    """))

    t4c8_study_1 = t4c8_instance.get_phenotype_data("study_1_pheno")

    pheno_categorical_collection = PersonSetCollection.from_families(
        config["pheno_cat"], families_fixture,
        t4c8_study_1.get_people_measure_values,
    )

    val3 = set(
        pheno_categorical_collection.person_sets["val3"].persons.keys(),
    )

    val4 = set(
        pheno_categorical_collection.person_sets["val4"].persons.keys(),
    )

    assert val3 == {("f2", "mom2"), ("f1", "mom1")}
    assert val4 == {("f2", "dad2")}


def test_phenotype_person_set_continuous(
    families_fixture: FamiliesData,
    t4c8_instance: GPFInstance,
) -> None:

    config = get_person_set_collections_config(textwrap.dedent("""
    [person_set_collections]
    selected_person_set_collections = ["pheno_cont"]

    pheno_cont.id = "pheno_cont"
    pheno_cont.name = "Phenotype measure continuous"
    pheno_cont.sources = [
        { from = "phenodb", source = "i1.iq" },
    ]
    pheno_cont.domain = [
        {id = "lower", name = "Lower",
         values = ["1"], color = "#ffffff"}
        {id = "higher", name = "Higher",
         values = ["3"], color = "#aabbcc"},
    ]
    pheno_cont.default = {id = "unknown", name = "Unknown", color="#ffffff"}
    """))

    study_1_pheno = t4c8_instance.get_phenotype_data("study_1_pheno")

    with pytest.raises(AssertionError) as excinfo:
        PersonSetCollection.from_families(
            config["pheno_cont"], families_fixture,
            study_1_pheno.get_people_measure_values,
        )

    assert (
        "Continuous measures not allowed in person sets! "
        "(i1.iq)") in str(excinfo.value)


def test_genotype_group_person_sets(
    t4c8_instance: GPFInstance,
) -> None:
    genotype_data_group = t4c8_instance.get_genotype_data(
        "t4c8_study_1",
    )
    assert genotype_data_group is not None
    phenotype_collection = genotype_data_group.get_person_set_collection(
        "phenotype",
    )
    assert phenotype_collection is not None

    expected_unaffected_persons = {
        ("f1.1", "mom1"), ("f1.1", "dad1"), ("f1.1", "s1"),
        ("f1.3", "mom3"), ("f1.3", "dad3"), ("f1.3", "s3"),
    }

    assert (
        set(phenotype_collection.person_sets["unaffected"].persons.keys())
        == expected_unaffected_persons
    )


def test_genotype_group_person_sets_overlapping(
    t4c8_instance: GPFInstance,
) -> None:
    genotype_data_group = t4c8_instance.get_genotype_data(
        "t4c8_study_2",
    )

    phenotype_collection = genotype_data_group.get_person_set_collection(
        "phenotype",
    )
    assert phenotype_collection is not None

    unaffected_persons = set(
        phenotype_collection.person_sets["unaffected"].persons.keys(),
    )
    assert "epilepsy" in phenotype_collection.person_sets

    epilepsy_persons = set(
        phenotype_collection.person_sets["epilepsy"].persons.keys(),
    )
    assert ("f2.1", "ch1") not in unaffected_persons
    assert ("f2.1", "ch1") in epilepsy_persons


def test_genotype_group_person_sets_subset(
    t4c8_instance: GPFInstance,
) -> None:
    genotype_data_group = t4c8_instance.get_genotype_data("t4c8_dataset")
    assert genotype_data_group is not None

    phenotype_collection = genotype_data_group.get_person_set_collection(
        "phenotype",
    )
    assert phenotype_collection is not None

    assert "autism" in phenotype_collection.person_sets
    assert "epilepsy" in phenotype_collection.person_sets

    autims_persons = set(
        phenotype_collection.person_sets["autism"].persons.keys(),
    )
    epilepsy_persons = set(
        phenotype_collection.person_sets["epilepsy"].persons.keys(),
    )
    assert {("f1.1", "p1"), ("f1.3", "p3")} == autims_persons
    assert {("f2.3", "ch3"), ("f2.1", "ch1")} == epilepsy_persons


@pytest.fixture
def families_fixture2(tmp_path: pathlib.Path) -> FamiliesData:
    ped_path = setup_pedigree(
        tmp_path / "test_pedigree2" / "ped2.ped",
        textwrap.dedent("""
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
    families = FamiliesLoader(ped_path).load()
    assert families is not None
    return families


def test_merge_person_sets(
    families_fixture: FamiliesData,
    families_fixture2: FamiliesData,
) -> None:

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
        config1["phenotype"], families_fixture)
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
        config2["phenotype"], families_fixture2)
    assert collection2.person_sets is not None, (config2, collection2)

    combined_families = FamiliesData.combine(
        families_fixture, families_fixture2)

    combined_collection = PersonSetCollection.combine(
        [collection1, collection2], combined_families)

    print(combined_collection)

    assert len(combined_collection) == 4


def test_combine_calls_merge_configs_with_single_collection(
    families_fixture: FamiliesData,
) -> None:
    content = textwrap.dedent("""
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
    config = get_person_set_collections_config(content)
    collection = PersonSetCollection.from_families(
        config["phenotype"], families_fixture,
    )

    with patch.object(
        PersonSetCollection,
        "merge_configs",
        wraps=PersonSetCollection.merge_configs,
    ) as mock_merge_configs:
        combined_collection = PersonSetCollection.combine(
            [collection], families_fixture,
        )

        # Assert that merge_configs was called
        mock_merge_configs.assert_called_once()

        # Assert that the combined collection has correctly updated values
        assert combined_collection.person_sets["aa"].values == ("aa",)
