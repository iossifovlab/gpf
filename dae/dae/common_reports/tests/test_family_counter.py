# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.common_reports.family_counter import (
    get_family_pedigree,
    FamilyCounter,
    FamiliesGroupCounters,
)


def test_family_counter(study1):
    person_set_collection = study1.get_person_set_collection("phenotype")
    family = study1.families["f5"]
    pedigree = get_family_pedigree(family, person_set_collection)
    family_counter = FamilyCounter.from_family(family, pedigree, 1)

    assert family_counter.pedigree[0] == (
        "f5",
        "mom5",
        "0",
        "0",
        "F",
        "mom",
        "#e35252",
        None,
        None,
        "",
        "",
    )
    assert family_counter.pedigree[1] == (
        "f5",
        "dad5",
        "0",
        "0",
        "M",
        "dad",
        "#aaaaaa",
        None,
        None,
        "",
        "",
    )
    assert family_counter.pedigree[2] == (
        "f5",
        "ch5",
        "mom5",
        "dad5",
        "F",
        "prb",
        "#e35252",
        None,
        None,
        "",
        "",
    )
    assert family_counter.pedigree[3] == (
        "f5",
        "ch5.1",
        "mom5",
        "dad5",
        "F",
        "sib",
        "#E0E0E0",
        None,
        True,
        "",
        "",
    )
    assert family_counter.pedigrees_count == 1

    assert len(family_counter.to_dict().keys()) == 3


@pytest.mark.xfail
def test_families_group_counter(study1):
    families_group_counter = FamiliesGroupCounters.from_families(
        study1.families,
        study1.get_person_set_collection("phenotype"),
        False,
        False,
    )

    assert len(families_group_counter.counters) == 8
    assert len(families_group_counter.counters[0].pedigree) == 3
    assert len(families_group_counter.counters[1].pedigree) == 3
    assert len(families_group_counter.counters[2].pedigree) == 4

    assert len(families_group_counter.to_dict().keys()) == 4


def test_families_group_counter_draw_all(study1):
    counter = FamiliesGroupCounters.from_families(
        study1.families,
        study1.get_person_set_collection("phenotype"),
        True,
        False,
    )
    assert len(counter.to_dict().keys()) == 4
    assert len(counter.counters) == len(study1.families)


def test_families_group_counter_same(study1):
    families_group_counter = FamiliesGroupCounters.from_families(
        study1.families,
        study1.get_person_set_collection("phenotype"),
        False,
        False,
    )
    assert len(families_group_counter.counters) == 8
    assert len(families_group_counter.to_dict().keys()) == 4


def test_families_group_counters(study1):
    families_group_counters = FamiliesGroupCounters.from_families(
        study1.families,
        study1.get_person_set_collection("phenotype"),
        False,
        False,
    )

    assert families_group_counters.group_name == "Diagnosis"

    assert len(families_group_counters.counters) == 8

    fg_dict = families_group_counters.to_dict()
    assert len(fg_dict.keys()) == 4
    assert len(fg_dict["legend"]) == 4
    assert (
        fg_dict["legend"][-1]["id"] == "unknown"
    )


def test_families_group_counter_study2(study2):
    families_group_counters = FamiliesGroupCounters.from_families(
        study2.families,
        study2.get_person_set_collection("phenotype"),
        False,
        False,
    )
    assert len(families_group_counters.counters) == 4
