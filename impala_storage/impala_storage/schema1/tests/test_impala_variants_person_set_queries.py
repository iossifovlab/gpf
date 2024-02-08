# pylint: disable=W0621,C0114,C0116,W0212,W0613
import io
import textwrap
from typing import cast, Any, Dict

from box import Box
import toml
import pytest

from dae.testing import convert_to_tab_separated
from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.person_sets import person_set_collections_schema
from dae.pedigrees.loader import FamiliesLoader
from dae.pedigrees.families_data import FamiliesData
from dae.person_sets import PersonSetCollection

from impala_storage.schema1.impala_variants import ImpalaVariants


@pytest.fixture
def families_fixture() -> FamiliesData:
    ped_content = io.StringIO(convert_to_tab_separated(
        """
            familyId personId dadId	 momId	sex status role
            f1       mom1     0      0      2   1      mom
            f1       dad1     0      0      1   1      dad
            f1       prb1     dad1   mom1   1   2      prb
            f1       sib1     dad1   mom1   2   2      sib
            f1       sib2     dad1   mom1   2   2      sib
            f2       grmom2   0      0      2   0      maternal_grandmother
            f2       grdad2   0      0      1   0      maternal_grandfather
            f2       mom2     grdad2 grmom2 2   1      mom
            f2       dad2     0      0      1   1      dad
            f2       prb2     dad2   mom2   1   2      prb
            f2       sib2_3   dad2   mom2   2   2      sib
        """))
    families = FamiliesLoader(ped_content).load()
    assert families is not None
    return families


def get_person_set_collections_config(content: str) -> Box:
    return cast(
        Box,
        GPFConfigParser.process_config(
            cast(Dict[str, Any], toml.loads(content)),
            {"person_set_collections": person_set_collections_schema},
        ).person_set_collections)


@pytest.fixture
def status_collection(families_fixture: FamiliesData) -> PersonSetCollection:
    content = textwrap.dedent(
        """
        [person_set_collections]
        selected_person_set_collections = ["status"]
        status.id = "status"
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

    config = get_person_set_collections_config(content)

    collection = PersonSetCollection.from_families(
        config.status, families_fixture)
    return collection


def test_status_person_set_collection(
    status_collection: PersonSetCollection
) -> None:
    assert status_collection is not None
    psc = status_collection

    assert len(psc.person_sets) == 3
    assert len(psc.person_sets["unknown"].persons) == 2
    assert len(psc.person_sets["affected"].persons) == 5
    assert len(psc.person_sets["unaffected"].persons) == 4


def test_status_person_set_collection_all_selected(
    status_collection: PersonSetCollection
) -> None:

    query = ImpalaVariants.build_person_set_collection_query(
        status_collection,
        ("status", {"affected", "unaffected", "unknown"})
    )

    assert query == ()


def test_status_person_set_collection_some_selected_no_default(
        status_collection: PersonSetCollection) -> None:

    query = ImpalaVariants.build_person_set_collection_query(
        status_collection,
        ("status", {"affected"})
    )

    assert query == ([{"status": "affected"}], [])


def test_status_person_set_collection_some_selected_and_default(
        status_collection: PersonSetCollection) -> None:

    query = ImpalaVariants.build_person_set_collection_query(
        status_collection,
        ("status", {"affected", "unknown"})
    )

    assert query == ([], [{"status": "unaffected"}])


@pytest.fixture
def status_sex_collection(
    families_fixture: FamiliesData
) -> PersonSetCollection:
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

    return PersonSetCollection.from_families(
        config.status_sex, families_fixture
    )


def test_status_sex_person_set_collection_all_selected(
        status_sex_collection: PersonSetCollection) -> None:

    query = ImpalaVariants.build_person_set_collection_query(
        status_sex_collection,
        ("status_sex", {
            "affected_male", "affected_female",
            "unaffected_male", "unaffected_female",
            "other"})
    )

    assert query == ()


def test_status_sex_person_set_collection_some_selected_no_default(
        status_sex_collection: PersonSetCollection) -> None:

    query = ImpalaVariants.build_person_set_collection_query(
        status_sex_collection,
        ("status_sex", {
            "affected_male", "affected_female"})
    )

    assert query == (
        [
            {"sex": "F", "status": "affected"},
            {"sex": "M", "status": "affected"},
        ], [])

    query = ImpalaVariants.build_person_set_collection_query(
        status_sex_collection,
        ("status_sex", {
            "unaffected_male", "unaffected_female"})
    )

    assert query == (
        [
            {"sex": "F", "status": "unaffected"},
            {"sex": "M", "status": "unaffected"}
        ], [])

    query = ImpalaVariants.build_person_set_collection_query(
        status_sex_collection,
        ("status_sex", {
            "affected_male", "unaffected_female"})
    )

    assert query == ([
        {"sex": "M", "status": "affected"},
        {"sex": "F", "status": "unaffected"},
    ], [])


def test_status_sex_person_set_collection_some_selected_with_default(
        status_sex_collection: PersonSetCollection) -> None:

    query = ImpalaVariants.build_person_set_collection_query(
        status_sex_collection,
        ("status_sex", {
            "affected_male", "affected_female", "other"})
    )

    assert query == ([], [
        {"sex": "F", "status": "unaffected"},
        {"sex": "M", "status": "unaffected"},
    ])

    query = ImpalaVariants.build_person_set_collection_query(
        status_sex_collection,
        ("status_sex", {
            "unaffected_male", "unaffected_female", "other"}))

    assert query == ([], [
        {"sex": "F", "status": "affected"},
        {"sex": "M", "status": "affected"},
    ])

    query = ImpalaVariants.build_person_set_collection_query(
        status_sex_collection,
        ("status_sex", {
            "affected_male", "unaffected_female", "other"})
    )

    assert query == ([], [
        {"sex": "F", "status": "affected"},
        {"sex": "M", "status": "unaffected"},
    ])
