# pylint: disable=W0621,C0114,C0116,W0212,W0613
from typing import Callable, cast

import pytest

from dae.pedigrees.family import Family
from dae.pedigrees.loader import FamiliesLoader

from dae.pedigrees.pedigrees import \
    Individual, \
    FamilyConnections, \
    MatingUnit, \
    SibshipUnit
from dae.pedigrees.family import Person

from dae.pedigrees.pedigrees import IntervalForVertex, \
    SandwichInstance, SandwichSolver
from dae.pedigrees.layout import IndividualWithCoordinates, Layout
from dae.pedigrees.families_data import FamiliesData


@pytest.fixture(scope="function")
def member1() -> Person:
    return Person(
        person_id="id1",
        family_id="fam1",
        mom_id="mom1",
        dad_id="dad1",
        sex="2",
        status="2",
        role="prb",
        layout="error",
        generated=False,
    )


@pytest.fixture(scope="function")
def member2() -> Person:
    return Person(
        person_id="mom1",
        family_id="fam1",
        mom_id="0",
        dad_id="0",
        sex="2",
        status="1",
        role="mom",
        layout="error",
        generated=False,
    )


@pytest.fixture(scope="function")
def member3() -> Person:
    return Person(
        person_id="dad1",
        family_id="fam1",
        mom_id="0",
        dad_id="0",
        sex="1",
        status="1",
        role="dad",
        layout="error",
        generated=True,
    )


@pytest.fixture(scope="function")
def member4() -> Person:
    return Person(
        person_id="id2",
        family_id="fam2",
        mom_id="mom2",
        dad_id="dad2",
        sex="1",
        status="2",
        role="prb",
        layout="2:100.0,75.0",
        generated=False,
    )


@pytest.fixture(scope="function")
def member5() -> Person:
    return Person(
        person_id="mom2",
        family_id="fam2",
        mom_id="0",
        dad_id="0",
        sex="2",
        status="1",
        role="mom",
        layout="1:50.0,50.0",
        generated=False,
    )


@pytest.fixture(scope="function")
def member6() -> Person:
    return Person(
        person_id="dad2",
        family_id="fam2",
        mom_id="0",
        dad_id="0",
        sex="1",
        status="1",
        role="dad",
        layout="1:50.0,100.0",
        generated=True,
    )


@pytest.fixture(scope="function")
def member7() -> Person:
    return Person(
        person_id="id3",
        family_id="fam3",
        mom_id="mom3",
        dad_id="0",
        sex="1",
        status="2",
        role="prb",
    )


@pytest.fixture(scope="function")
def individual4(member4: Person) -> Individual:
    return Individual(member=member4)


@pytest.fixture(scope="function")
def individual5(member5: Person) -> Individual:
    return Individual(member=member5)


@pytest.fixture(scope="function")
def individual6(member6: Person) -> Individual:
    return Individual(member=member6)


@pytest.fixture(scope="function")
def family1(member1: Person, member2: Person, member3: Person) -> Family:
    return Family.from_persons([member1, member2, member3])


@pytest.fixture(scope="function")
def family2(member4: Person, member5: Person, member6: Person) -> Family:
    return Family.from_persons([member4, member5, member6])


@pytest.fixture(scope="function")
def family3(member7: Person) -> Family:
    return Family.from_persons([member7])


@pytest.fixture(scope="function")
def sibship_unit2(individual4: Individual) -> SibshipUnit:
    return SibshipUnit({individual4})


@pytest.fixture(scope="function")
def mating_unit2(
    individual5: Individual,
    individual6: Individual,
    sibship_unit2: SibshipUnit
) -> MatingUnit:
    return MatingUnit(individual5, individual6, sibship_unit2)


# @pytest.fixture(scope="function")
# def people1(member1, member2, member3):
#     return {"fam1;id1": member1, "fam1;mom1": member2, "fam1;dad1": member3}


# @pytest.fixture(scope="function")
# def people2(member4, member5, member6):
#     return {"fam2;id2": member4, "fam2;mom2": member5, "fam2;dad2": member6}


@pytest.fixture(scope="function")
def layout2(
    individual4: Individual,
    individual5: Individual,
    individual6: Individual
) -> Layout:
    layout = Layout()
    layout._id_to_position = {
        individual4: IndividualWithCoordinates(individual4, 100.0, 75.0),
        individual5: IndividualWithCoordinates(individual5, 50.0, 50.0),
        individual6: IndividualWithCoordinates(individual6, 50.0, 100.0),
    }
    layout._individuals_by_rank = [[individual5, individual6], [individual4]]
    return layout


@pytest.fixture(scope="function")
def family_connections_from_family2(family2: Family) -> FamilyConnections:
    result = FamilyConnections.from_family(family2)
    assert result is not None
    return result


@pytest.fixture(scope="function")
def sandwich_instance_from_family2(
    family_connections_from_family2: FamilyConnections
) -> SandwichInstance:
    return family_connections_from_family2.create_sandwich_instance()


@pytest.fixture(scope="function")
def intervals_from_family2(
    sandwich_instance_from_family2: SandwichInstance
) -> list[IntervalForVertex]:
    return cast(
        list[IntervalForVertex],
        SandwichSolver.solve(sandwich_instance_from_family2))


@pytest.fixture(scope="function")
def individuals_intervals_from_family2(
    intervals_from_family2: list[IntervalForVertex]
) -> list[IntervalForVertex]:
    return [
        interval
        for interval in intervals_from_family2
        if interval.vertex.is_individual()
    ]


@pytest.fixture(scope="function")
def layout_from_family2(
    individuals_intervals_from_family2: list[IntervalForVertex]
) -> list[Layout]:
    return [Layout(individuals_intervals_from_family2)]


@pytest.fixture(scope="session")
def pedigree_test(fixture_dirname: Callable) -> FamiliesData:
    loader = FamiliesLoader(fixture_dirname("pedigrees/test.ped"))
    families = loader.load()
    return families


@pytest.fixture(scope="session")
def fam1(pedigree_test: FamiliesData) -> Family:
    return pedigree_test["fam1"]


@pytest.fixture(scope="session")
def fam1_family_connections(fam1: Family) -> FamilyConnections:
    result = FamilyConnections.from_family(fam1)
    assert result is not None
    return result
