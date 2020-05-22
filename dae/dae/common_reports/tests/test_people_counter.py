from dae.common_reports.people_counter import PeopleCounter, PeopleCounters


def test_people_counter(study1, phenotype_role_collection):
    people_counter = PeopleCounter(
        study1.families,
        phenotype_role_collection.person_sets["phenotype1"],
    )

    assert people_counter.people_male == 7
    assert people_counter.people_female == 9
    assert people_counter.people_unspecified == 0
    assert people_counter.people_total == 16

    assert people_counter.is_empty() is False
    assert people_counter.is_empty_field("people_male") is False
    assert people_counter.is_empty_field("people_female") is False

    assert (
        len(people_counter.to_dict([
            "people_male", "people_female", "people_total"
        ]).keys()) == 4
    )


def test_people_counter_empty(study1, phenotype_role_collection):
    people_counter = PeopleCounter(
        study1.families,
        phenotype_role_collection.person_sets["unknown"],
    )

    assert people_counter.people_male == 4
    assert people_counter.people_female == 0
    assert people_counter.people_unspecified == 0
    assert people_counter.people_total == 4

    assert people_counter.is_empty() is False
    assert people_counter.is_empty_field("people_female") is True

    assert len(people_counter.to_dict([]).keys()) == 1


def test_people_counters(study1, phenotype_role_collection):
    people_counters = PeopleCounters(
        study1.families, phenotype_role_collection
    )

    assert len(people_counters.counters) == 4
    assert people_counters.group_name == "Diagnosis"
    assert people_counters.rows == [
        "people_male",
        "people_female",
        "people_total",
    ]
    assert sorted(people_counters.column_names) == sorted(
        [
            "phenotype 1",
            "phenotype 2",
            "unaffected",
            "unknown",
        ]
    )

    assert len(people_counters.to_dict().keys()) == 4
