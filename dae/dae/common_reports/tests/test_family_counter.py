# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.common_reports.family_counter import (
    get_family_pedigree,
    FamilyCounter,
    FamiliesGroupCounters,
)
from dae.studies.study import GenotypeDataStudy


def test_family_counter(study1: GenotypeDataStudy) -> None:
    person_set_collection = study1.get_person_set_collection("phenotype")
    assert person_set_collection is not None

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

    assert len(family_counter.to_dict().keys()) == 4


def test_family_counter_tags(study1: GenotypeDataStudy) -> None:
    person_set_collection = study1.get_person_set_collection("phenotype")
    assert person_set_collection is not None

    family = study1.families["f6"]
    pedigree = get_family_pedigree(family, person_set_collection)
    family_counter = FamilyCounter.from_family(family, pedigree, 1)

    assert isinstance(family_counter.tags, list)

    assert set(family_counter.tags) == set([
        "tag_simplex_family",
        "tag_trio_family",
        "tag_nuclear_family",
        "tag_affected_prb_family",
        # "tag_family_type:type#3",
        "tag_male_prb_family",
        "tag_unaffected_dad_family",
        "tag_unaffected_mom_family"
    ])


def test_families_group_counter_draw_all(study1: GenotypeDataStudy) -> None:
    collection = study1.get_person_set_collection("phenotype")
    assert collection is not None

    counter = FamiliesGroupCounters.from_families(
        study1.families,
        collection,
        True,
    )
    assert len(counter.to_dict().keys()) == 4
    assert len(counter.counters) == len(study1.families)


def test_families_group_counter_same(study1: GenotypeDataStudy) -> None:
    collection = study1.get_person_set_collection("phenotype")
    assert collection is not None

    families_group_counter = FamiliesGroupCounters.from_families(
        study1.families,
        collection,
        False,
    )
    assert len(families_group_counter.counters) == 8
    assert len(families_group_counter.to_dict().keys()) == 4


def test_families_group_counters(study1: GenotypeDataStudy) -> None:
    collection = study1.get_person_set_collection("phenotype")
    assert collection is not None

    families_group_counters = FamiliesGroupCounters.from_families(
        study1.families,
        collection,
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


def test_families_group_counter_study2(study2: GenotypeDataStudy) -> None:
    collection = study2.get_person_set_collection("phenotype")
    assert collection is not None

    families_group_counters = FamiliesGroupCounters.from_families(
        study2.families,
        collection,
        False,
    )
    assert len(families_group_counters.counters) == 4
