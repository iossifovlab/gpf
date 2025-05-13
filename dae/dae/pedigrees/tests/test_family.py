# pylint: disable=W0621,C0114,C0116,W0212,W0613

from dae.gpf_instance.gpf_instance import GPFInstance


def test_families_of_persons(
    t4c8_instance: GPFInstance,
) -> None:
    genotype_data = t4c8_instance.get_genotype_data("t4c8_study_1")
    person_ids = {"mom1", "dad1", "p1", "s3"}
    assert genotype_data.families.families_of_persons(person_ids) == {
        "f1.1", "f1.3",
    }
