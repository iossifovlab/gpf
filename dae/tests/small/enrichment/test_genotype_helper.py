# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest
from dae.studies.study import GenotypeData


@pytest.mark.parametrize(
    "person_set_id,male,female,unspecified",
    [
        ("phenotype1", 1, 1, 0),
        ("unaffected", 0, 1, 0),
    ],
)
def test_get_children_stats(
    f1_trio: GenotypeData,
    person_set_id: str,
    male: int, female: int, unspecified: int,
) -> None:
    psc = f1_trio.get_person_set_collection("phenotype")
    assert psc is not None

    children_stats = psc.person_sets[person_set_id].get_children_stats()

    assert children_stats.male == male
    assert children_stats.female == female
    assert children_stats.unspecified == unspecified
