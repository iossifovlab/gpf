import os
import pytest

from dae.variants.attributes import Role
from dae.pedigrees.loader import FamiliesLoader
from dae.pedigrees.pedigrees import FamilyConnections


@pytest.fixture(scope="session")
def families_loader(request):
    def builder(relpath):
        filename = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "fixtures", relpath
        )
        loader = FamiliesLoader(filename, ped_sep=",")
        families = loader.load()
        return families

    return builder


def test_not_connected_aunts(families_loader):
    families = families_loader("test_not_connected_aunts.csv")
    assert families is not None

    fam = families["fam1"]
    assert fam is not None

    family_connections = FamilyConnections.from_family(fam)
    assert family_connections is not None

    print(family_connections.get_mating_units())
    print(family_connections.get_sibship_units())

    g = family_connections.get_graph()
    print(g)

    assert not family_connections.is_connected()

    for comp in family_connections.connected_components():
        print(comp, type(comp))


def test_not_connected_aunts_roles(families_loader):
    families = families_loader("test_not_connected_aunts.csv")
    assert families is not None

    fam = families["fam1"]
    assert len(fam) == 7
    assert len(fam.full_members) == 7

    fc = FamilyConnections.from_family(fam)

    fam1 = fc.family
    assert len(fam) == 7
    assert len(fam1.full_members) == 9
    print(fam1.full_members)

    aunt = fam1.get_member("aunt1")
    assert aunt.role == Role.unknown

    aunt_mating = fam.get_member("aunt1.father")
    assert aunt_mating.role == Role.unknown
