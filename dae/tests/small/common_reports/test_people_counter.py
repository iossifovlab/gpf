# pylint: disable=W0621,C0114,C0116,W0212,W0613
from dae.common_reports.people_counter import PeopleCounter, PeopleReport
from dae.person_sets import PersonSetCollection


def test_people_counter(
    phenotype_role_collection: PersonSetCollection,
) -> None:
    people_counter = PeopleCounter.from_person_set(
        phenotype_role_collection.person_sets["autism"],
    )

    assert people_counter.people_male == 0
    assert people_counter.people_female == 2
    assert people_counter.people_unspecified == 0
    assert people_counter.people_total == 2

    assert people_counter.is_empty() is False
    assert people_counter.is_empty_field("people_male") is True
    assert people_counter.is_empty_field("people_female") is False

    assert (
        len(people_counter.to_dict([
            "people_male", "people_female", "people_total",
        ]).keys()) == 4
    )


def test_people_counter_unspecified(
    phenotype_role_collection: PersonSetCollection,
) -> None:
    people_counter = PeopleCounter.from_person_set(
        phenotype_role_collection.person_sets["unspecified"],
    )

    assert people_counter.people_male == 0
    assert people_counter.people_female == 1
    assert people_counter.people_unspecified == 0
    assert people_counter.people_total == 1

    assert people_counter.is_empty() is False
    assert people_counter.is_empty_field("people_male") is True

    assert len(people_counter.to_dict([]).keys()) == 1


def test_people_report(
    phenotype_role_collection: PersonSetCollection,
) -> None:
    people_report = PeopleReport.from_person_set_collections(
        [phenotype_role_collection],
    )

    assert len(people_report.people_counters) == 1
    people_counters = people_report.people_counters[0]
    assert len(people_counters.counters) == 4
    assert people_counters.group_name == "Phenotype"
    assert people_counters.rows == [
        "people_male",
        "people_female",
        "people_total",
    ]
    assert sorted(people_counters.columns) == sorted(
        [
            "autism",
            "epilepsy",
            "unaffected",
            "unspecified",
        ],
    )

    assert len(people_counters.to_dict().keys()) == 4
