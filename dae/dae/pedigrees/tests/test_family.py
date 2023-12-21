# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.gpf_instance.gpf_instance import GPFInstance


def test_families_of_persons(fixtures_gpf_instance: GPFInstance) -> None:
    genotype_data = fixtures_gpf_instance.get_genotype_data("Study1")
    person_ids = {"ch1", "ch3", "ch5", "ch5.1", "ch7", "ch11"}
    assert genotype_data.families.families_of_persons(person_ids) == {
        "f1", "f3", "f5", "f7", "f11"
    }
