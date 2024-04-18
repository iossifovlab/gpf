# pylint: disable=W0621,C0114,C0116,W0212,W0613
from dae.pedigrees.families_data import FamiliesData
from dae.pedigrees.family import Family, Person
from dae.pedigrees.pedigrees import (
    FamilyConnections,
    Individual,
    MatingUnit,
    SibshipUnit,
)
from dae.variants.attributes import Role, Sex

NO_RANK = -3673473456


def test_pedigree_member(member4: Person) -> None:
    assert member4.person_id == "id2"
    assert member4.role == Role.prb

    assert member4.get_attr("person_id") == "id2"
    assert member4.get_attr("sex") == Sex.M
    # assert member['phenotype'] == 'affected'

    # assert sorted(list(member.keys())) == sorted([
    #     "family_id", "person_id", "sample_id", "sex", "role", "status",
    #     "mom_id", "dad_id", "layout", "generated", # "phenotype"
    # ])


def test_pedigree(family2: Family, member1: Person, member2: Person) -> None:
    assert len(family2.full_members) == 3
    assert len(family2.members_in_order) == 2

    assert family2.family_id == "fam2"
    member1.family_id = "fam2"
    member2.family_id = "fam2"
    family2.add_members([member1, member2])
    assert len(family2.full_members) == 5

    assert len(family2.members_in_order) == 4


def test_sibship_unit(
    sibship_unit2: SibshipUnit, individual4: Individual,
) -> None:
    assert len(sibship_unit2.individual_set()) == 1
    assert individual4 in sibship_unit2.individual_set()

    assert len(sibship_unit2.children_set()) == 0


def test_mating_unit(
    mating_unit2: MatingUnit,
    individual4: Individual,
    individual5: Individual,
    individual6: Individual,
) -> None:
    assert len(mating_unit2.individual_set()) == 2
    assert individual5 in mating_unit2.individual_set()
    assert individual6 in mating_unit2.individual_set()

    assert len(mating_unit2.children_set()) == 1
    assert individual4 in mating_unit2.children_set()

    assert mating_unit2.other_parent(individual5) == individual6


def test_individual(
    individual4: Individual,
    individual5: Individual,
    individual6: Individual,
    mating_unit2: MatingUnit,
) -> None:
    individual5.mating_units.append(mating_unit2)
    individual6.mating_units.append(mating_unit2)

    assert individual5.member is not None
    assert individual5.member.person_id == "mom2"

    assert len(individual5.individual_set()) == 1
    assert individual5 in individual5.individual_set()

    assert len(individual5.children_set()) == 1
    assert individual4 in individual5.children_set()

    assert individual4.rank == NO_RANK
    assert individual5.rank == NO_RANK
    assert individual6.rank == NO_RANK
    individual5.add_rank(1)
    assert individual4.rank == 0
    assert individual5.rank == 1
    assert individual6.rank == 1

    assert str(individual5) == "mom2"

    assert individual5.are_siblings(individual6) is False
    assert individual5.are_mates(individual6) is True

    assert individual5.is_individual() is True


def test_family_connections_valid(mating_unit2: MatingUnit) -> None:
    id_to_mating_unit = {"mom2,dad2": mating_unit2}
    assert FamilyConnections.is_valid_family(id_to_mating_unit) is True


def test_family_connections_invalid(
    individual4: Individual,
    individual5: Individual,
    individual6: Individual,
) -> None:
    id_to_mating_unit = [
        {
            "mom2,dad2": MatingUnit(
                Individual(), individual6, SibshipUnit([individual4]),
            ),
        },
        {
            "mom2,dad2": MatingUnit(
                individual5, Individual(), SibshipUnit([individual4]),
            ),
        },
        {
            "mom2,dad2": MatingUnit(
                individual5, individual6, SibshipUnit([Individual()]),
            ),
        },
    ]

    assert FamilyConnections.is_valid_family(id_to_mating_unit[0]) is False
    assert FamilyConnections.is_valid_family(id_to_mating_unit[1]) is False
    assert FamilyConnections.is_valid_family(id_to_mating_unit[2]) is False


def test_family2_connections(family2: Family) -> None:
    assert len(family2.full_members) == 3
    FamilyConnections.add_missing_members(family2)
    assert len(family2.full_members) == 3
    ids = [member.person_id for member in family2.full_members]
    assert len(ids) == 3
    assert sorted(ids) == sorted(["id2", "mom2", "dad2"])


def test_family3_connections(family3: Family) -> None:
    assert len(family3.full_members) == 1
    FamilyConnections.add_missing_members(family3)
    assert len(family3.full_members) == 3
    ids = [member.person_id for member in family3.full_members]
    assert len(ids) == 3
    assert sorted(ids) == sorted(["id3", "mom3", "mom3.father"])


# def test_family_connections_add_missing_members(family2, family3):

#     family2._members_in_order = list(filter(
#         lambda member: member.person_id != 'mom2', family2.members_in_order
#     ))
#     prb = list(filter(
#         lambda member: member.person_id == 'id2', family2.members_in_order
#     ))
#     assert len(prb) == 1
#     prb[0].mother = '0'
#     assert len(family2) == 2
#     FamilyConnections.add_missing_members(family2)
#     assert len(family2.members) == 3
#     ids = [member.person_id for member in family2.members]
#     assert len(ids) == 3
#     assert sorted(ids) == sorted(['id2', 'dad2', 'dad2.mother'])


def test_family_connections_from_family1_simple(family1: Family) -> None:
    family_connections = FamilyConnections.from_family(family1)
    assert family_connections is not None


def test_family_connections_from_family_simple(family2: Family) -> None:
    family_connections = FamilyConnections.from_family(family2)
    assert family_connections is not None

    assert len(family_connections.members) == 3

    sandwich_instance = family_connections.create_sandwich_instance()
    assert len(sandwich_instance.vertices) == 5
    assert len(sandwich_instance.required_graph) == 5
    assert len(sandwich_instance.forbidden_graph) == 5

    individuals_with_rank = family_connections.get_individuals_with_rank(1)
    assert len(individuals_with_rank) == 1

    persons_with_rank = set()
    for individual in individuals_with_rank:
        assert individual.member is not None
        persons_with_rank.add(individual.member.person_id)

    assert "id2" in persons_with_rank


def test_family_connections_from_family_add_members_one_member(
    family3: Family,
) -> None:
    family_connections = FamilyConnections.from_family(
        family3, add_missing_members=True,
    )
    assert family_connections is not None

    assert len(family_connections.members) == 3

    sandwich_instance = family_connections.create_sandwich_instance()
    assert len(sandwich_instance.vertices) == 5
    assert len(sandwich_instance.required_graph) == 5
    assert len(sandwich_instance.forbidden_graph) == 5

    individuals_with_rank = family_connections.get_individuals_with_rank(1)
    assert len(individuals_with_rank) == 1
    persons_with_rank = set()
    for individual in individuals_with_rank:
        assert individual.member is not None
        persons_with_rank.add(individual.member.person_id)
    assert "id3" in persons_with_rank


def test_family_connections_from_family_one_member(family3: Family) -> None:
    assert (
        FamilyConnections.from_family(family3, add_missing_members=False)
        is None
    )


def test_family_connections_from_family_add_members(family2: Family) -> None:
    del family2.persons["mom2"]
    prb = family2.persons["id2"]
    prb.mom_id = None
    family2.redefine()

    family_connections = FamilyConnections.from_family(
        family2, add_missing_members=True,
    )
    assert family_connections is not None

    assert len(family_connections.members) == 3

    sandwich_instance = family_connections.create_sandwich_instance()
    assert len(sandwich_instance.vertices) == 5
    assert len(sandwich_instance.required_graph) == 5
    assert len(sandwich_instance.forbidden_graph) == 5

    individuals_with_rank = family_connections.get_individuals_with_rank(1)
    assert len(individuals_with_rank) == 1
    persons_with_rank = set()
    for individual in individuals_with_rank:
        assert individual.member is not None
        persons_with_rank.add(individual.member.person_id)
    assert "id2" in persons_with_rank


def test_family_connections_from_family_do_not_add_members(
    family3: Family,
) -> None:
    assert (
        FamilyConnections.from_family(family3, add_missing_members=False)
        is None
    )

    # family2._members_in_order = list(filter(
    #     lambda member: member.person_id != 'mom2', family2.members_in_order
    # ))
    # prb = list(filter(
    #     lambda member: member.person_id == 'id2', family2.members_in_order
    # ))
    # assert len(prb) == 1
    # prb[0].mother = '0'
    # print(len(family2))
    # assert FamilyConnections.from_family(
    #     family2, add_missing_members=False) is None


def test_reading_pedigree_file(pedigree_test: FamiliesData) -> None:
    assert pedigree_test is not None


def test_family_connections_can_be_created(
    fam1_family_connections: FamilyConnections,
) -> None:
    assert fam1_family_connections is not None


def test_sandwich_instance_can_be_created_for_fam1(
    fam1_family_connections: FamilyConnections,
) -> None:
    sandwich = fam1_family_connections.create_sandwich_instance()

    assert sandwich is not None
