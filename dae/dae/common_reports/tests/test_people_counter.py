import pytest

from dae.common_reports.people_counter import PeopleCounter, PeopleCounters
from dae.person_sets import PersonSetCollection


@pytest.fixture
def phenotype_role_collection(study1):
    return PersonSetCollection.compose(
        study1.get_person_set_collection("phenotype"),
        study1.get_person_set_collection("role"),
        name="Role and Diagnosis",
    )


def test_people_counter(study1, phenotype_role_collection):
    people_counter = PeopleCounter(
        study1.families,
        phenotype_role_collection.person_sets["phenotype1.mom"],
    )

    assert people_counter.people_male == 0
    assert people_counter.people_female == 4
    assert people_counter.people_unspecified == 0
    assert people_counter.people_total == 4

    assert people_counter.is_empty() is False
    assert people_counter.is_empty_field("people_male") is True
    assert people_counter.is_empty_field("people_female") is False

    assert (
        len(people_counter.to_dict(["people_female", "people_total"]).keys())
        == 3
    )


def test_people_counter_empty(study1, phenotype_role_collection):
    people_counter = PeopleCounter(
        study1.families,
        phenotype_role_collection.person_sets["phenotype1.dad"],
    )

    assert people_counter.people_male == 0
    assert people_counter.people_female == 0
    assert people_counter.people_unspecified == 0
    assert people_counter.people_total == 0

    assert people_counter.is_empty() is True
    assert people_counter.is_empty_field("people_male") is True

    assert len(people_counter.to_dict([]).keys()) == 1


def test_people_counters(study1, phenotype_role_collection):
    people_counters = PeopleCounters(
        study1.families, phenotype_role_collection
    )

    assert len(people_counters.counters) == 8
    assert people_counters.group_name == "Role and Diagnosis"
    assert people_counters.rows == [
        "people_male",
        "people_female",
        "people_total",
    ]
    assert sorted(people_counters.column_names) == sorted(
        [
            "phenotype1.sib",
            "phenotype2.sib",
            "phenotype1.prb",
            "phenotype2.prb",
            "unaffected.prb",
            "unaffected.mom",
            "phenotype1.mom",
            "unaffected.dad",
        ]
    )

    assert len(people_counters.to_dict().keys()) == 4
