# pylint: disable=W0621,C0114,C0116,W0212,W0613
import pytest

from dae.variants.attributes import Role
from dae.pedigrees.family import FamilyType, Person, Family
from dae.pedigrees.families_data import FamiliesData


def trio_persons(family_id: str = "trio_family") -> list[Person]:
    return [
        Person(**{
            "family_id": family_id,
            "person_id": "mom",
            "sex": "F",
            "role": "mom",
            "status": 1
        }),
        Person(**{
            "family_id": family_id,
            "person_id": "dad",
            "sex": "M",
            "role": "dad",
            "status": 1
        }),
        Person(**{
            "family_id": family_id,
            "person_id": "p1",
            "sex": "M",
            "role": "prb",
            "status": 2
        }),
    ]


@pytest.fixture
def quad_persons() -> list[Person]:
    persons = trio_persons("quad_family")
    persons.append(Person(**{
        "family_id": "quad_family",
        "person_id": "s1",
        "sex": "M",
        "role": "sib",
        "status": 1
    }))
    return persons


@pytest.fixture
def multigenerational_persons() -> list[Person]:
    persons = trio_persons("multigenerational_family")
    persons.append(Person(**{
        "family_id": "multigenerational_family",
        "person_id": "grandparent",
        "sex": "M",
        "role": str(Role.maternal_grandfather),
        "status": 1
    }))
    return persons


@pytest.fixture
def simplex_persons() -> list[Person]:
    persons = trio_persons("simplex_family")
    persons[0]._status = 2  # type: ignore
    persons[0]._attributes["status"] = 2
    return persons


@pytest.fixture
def simplex_persons_2() -> list[Person]:
    persons = trio_persons("simplex_family")
    persons[0]._status = 2  # type: ignore
    persons[0]._attributes["status"] = 2
    persons.append(Person(**{
        "family_id": "simplex_family",
        "person_id": "s1",
        "sex": "M",
        "role": "sib",
        "status": 1
    }))
    return persons


@pytest.fixture
def multiplex_persons() -> list[Person]:
    persons = trio_persons("multiplex_family")
    persons.append(Person(**{
        "family_id": "multiplex_family",
        "person_id": "s1",
        "sex": "M",
        "role": "sib",
        "status": 2
    }))
    return persons


def test_family_type_trio() -> None:
    family = Family.from_persons(trio_persons())
    assert family.family_type is FamilyType.TRIO


def test_family_type_quad(quad_persons: list[Person]) -> None:
    family = Family.from_persons(quad_persons)
    assert family.family_type is FamilyType.QUAD


@pytest.mark.parametrize("role", [
    (Role.maternal_grandfather),
    (Role.paternal_grandfather),
    (Role.maternal_grandmother),
    (Role.paternal_grandmother),
])
def test_family_type_multigenerational(role: Role) -> None:
    persons = list(trio_persons("multigenerational"))
    persons.append(Person(**{
        "family_id": "multigenerational",
        "person_id": "grandparent",
        "sex": "U",
        "role": str(role),
        "status": 1
    }))
    family = Family.from_persons(persons)
    assert family.family_type is FamilyType.MULTIGENERATIONAL


def test_family_type_simplex(simplex_persons: list[Person]) -> None:
    family = Family.from_persons(simplex_persons)
    assert family.family_type is FamilyType.SIMPLEX


def test_family_type_simplex_2(simplex_persons_2: list[Person]) -> None:
    family = Family.from_persons(simplex_persons_2)
    assert family.family_type is FamilyType.SIMPLEX


def test_family_type_multiplex(multiplex_persons: list[Person]) -> None:
    family = Family.from_persons(multiplex_persons)
    assert family.family_type is FamilyType.MULTIPLEX


def test_families_data_families_by_type(
    quad_persons: list[Person],
    multigenerational_persons: list[Person],
    simplex_persons: list[Person],
    multiplex_persons: list[Person]
) -> None:
    families_data = FamiliesData.from_families(
        {
            "trio_family": Family.from_persons(trio_persons()),
            "quad_family": Family.from_persons(quad_persons),
            "multigenerational_family":
                Family.from_persons(multigenerational_persons),
            "simplex_family": Family.from_persons(simplex_persons),
            "multiplex_family": Family.from_persons(multiplex_persons),
        }
    )
    assert families_data.families_by_type == {
        FamilyType.QUAD: {"quad_family"},
        FamilyType.TRIO: {"trio_family"},
        FamilyType.MULTIGENERATIONAL: {"multigenerational_family"},
        FamilyType.SIMPLEX: {"simplex_family"},
        FamilyType.MULTIPLEX: {"multiplex_family"},
    }
