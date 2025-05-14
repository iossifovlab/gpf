# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.common_reports.family_counter import (
    FamiliesGroupCounters,
    FamilyCounter,
    get_family_pedigree,
)
from dae.studies.study import GenotypeData


def test_family_counter(t4c8_dataset: GenotypeData) -> None:
    person_set_collection = t4c8_dataset.get_person_set_collection("phenotype")
    assert person_set_collection is not None

    family = t4c8_dataset.families["f1.1"]
    pedigree = get_family_pedigree(family, person_set_collection)
    family_counter = FamilyCounter.from_family(family, pedigree, 1)

    assert family_counter.pedigree[0][:7] == (
        "f1.1",
        "mom1",
        "0",
        "0",
        "F",
        "mom",
        "#ffffff",
    )
    assert family_counter.pedigree[1][:7] == (
        "f1.1",
        "dad1",
        "0",
        "0",
        "M",
        "dad",
        "#ffffff",
    )
    assert family_counter.pedigree[2][:7] == (
        "f1.1",
        "p1",
        "mom1",
        "dad1",
        "F",
        "prb",
        "#ff2121",
    )
    assert family_counter.pedigree[3][:7] == (
        "f1.1",
        "s1",
        "mom1",
        "dad1",
        "M",
        "sib",
        "#ffffff",
    )
    assert family_counter.pedigrees_count == 1

    assert len(family_counter.to_dict().keys()) == 4


def test_family_counter_tags(t4c8_dataset: GenotypeData) -> None:
    person_set_collection = t4c8_dataset.get_person_set_collection("phenotype")
    assert person_set_collection is not None

    family = t4c8_dataset.families["f1.1"]
    pedigree = get_family_pedigree(family, person_set_collection)
    family_counter = FamilyCounter.from_family(family, pedigree, 1)

    assert isinstance(family_counter.tags, list)

    assert set(family_counter.tags) == {
        "tag_simplex_family",
        "tag_quad_family",
        "tag_nuclear_family",
        "tag_affected_prb_family",
        "tag_female_prb_family",
        "tag_unaffected_dad_family",
        "tag_unaffected_mom_family",
        "tag_unaffected_sib_family",
    }


def test_families_group_counter_draw_all(t4c8_dataset: GenotypeData) -> None:
    collection = t4c8_dataset.get_person_set_collection("phenotype")
    assert collection is not None

    counter = FamiliesGroupCounters.from_families(
        t4c8_dataset.families,
        collection,
        draw_all_families=True,
    )
    assert len(counter.to_dict().keys()) == 4
    assert len(counter.counters) == len(t4c8_dataset.families)


def test_families_group_counter_same(t4c8_dataset: GenotypeData) -> None:
    collection = t4c8_dataset.get_person_set_collection("phenotype")
    assert collection is not None

    families_group_counter = FamiliesGroupCounters.from_families(
        t4c8_dataset.families,
        collection,
        draw_all_families=False,
    )
    assert len(families_group_counter.counters) == 4
    assert len(families_group_counter.to_dict().keys()) == 4


def test_families_group_counters(t4c8_dataset: GenotypeData) -> None:
    collection = t4c8_dataset.get_person_set_collection("phenotype")
    assert collection is not None

    families_group_counters = FamiliesGroupCounters.from_families(
        t4c8_dataset.families,
        collection,
        draw_all_families=False,
    )

    assert families_group_counters.group_name == "Phenotype"

    assert len(families_group_counters.counters) == 4

    fg_dict = families_group_counters.to_dict()
    assert len(fg_dict.keys()) == 4
    assert len(fg_dict["legend"]) == 4
    assert (
        fg_dict["legend"][-1]["id"] == "unspecified"
    )


def test_families_group_counter_study2(t4c8_dataset: GenotypeData) -> None:
    collection = t4c8_dataset.get_person_set_collection("phenotype")
    assert collection is not None

    families_group_counters = FamiliesGroupCounters.from_families(
        t4c8_dataset.families,
        collection,
        draw_all_families=False,
    )
    assert len(families_group_counters.counters) == 4
