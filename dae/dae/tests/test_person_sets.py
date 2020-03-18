import pytest

from dae.configuration.gpf_config_parser import GPFConfigParser
from dae.configuration.schemas.person_sets import person_set_collections_schema
from dae.pedigrees.loader import FamiliesLoader
from dae.person_sets import produce_sets, from_pedigree, PersonSet


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
    people_sets = produce_sets(config.status)
    assert people_sets == {
        "affected": PersonSet(
            "affected", "Affected", "affected_val", "#aabbcc", list()
        ),
        "unaffected": PersonSet(
            "unaffected", "Unaffected", "unaffected_val", "#ffffff", list()
        ),
    }


def test_from_pedigree(fixture_dirname):
    config = get_person_set_collections_config(
        fixture_dirname("quads_f1_person_sets.toml")
    )
    quads_f1_families = FamiliesLoader(
        fixture_dirname("studies/quads_f1/data/quads_f1.ped")
    ).load()
    status_collection = from_pedigree(config.status, quads_f1_families)

    result_person_ids = set(
        (
            person.person_id
            for person in status_collection.person_sets["affected"].persons
        )
    )
    assert result_person_ids == {
        "prb1",
        "sib1",
        "sib2",
    }


def test_from_pedigree_missing_value_in_domain(fixture_dirname):
    config = get_person_set_collections_config(
        fixture_dirname("quads_f1_person_sets_incomplete_domain.toml")
    )
    quads_f1_families = FamiliesLoader(
        fixture_dirname("studies/quads_f1/data/quads_f1.ped")
    ).load()

    with pytest.raises(AssertionError) as excinfo:
        from_pedigree(
            config.status, quads_f1_families,
        )
    assert "Domain for 'status' does not have the value 'affected'!" in str(
        excinfo.value
    )


def test_from_pedigree_nonexistent_domain(fixture_dirname):
    config = get_person_set_collections_config(
        fixture_dirname("quads_f1_person_sets_nonexistent_domain.toml")
    )
    quads_f1_families = FamiliesLoader(
        fixture_dirname("studies/quads_f1/data/quads_f1.ped")
    ).load()

    with pytest.raises(AssertionError) as excinfo:
        from_pedigree(
            config.invalid, quads_f1_families,
        )

    assert "Missing domain value for 'invalid' in person" in str(excinfo.value)
