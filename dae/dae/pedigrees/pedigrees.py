#!/usr/bin/env python
import abc

from collections import defaultdict
from functools import reduce
from typing import Any, cast
import networkx as nx  # type: ignore

from dae.pedigrees.interval_sandwich import SandwichInstance
from dae.variants.attributes import Role, Sex, Status
from dae.pedigrees.family import Person, Family


class FamilyConnections():
    """Representation of connections between family members."""

    def __init__(self, family, id_to_individual, id_to_mating_unit):
        assert family is not None
        assert "0" not in id_to_individual
        assert "" not in id_to_individual

        self.family = family
        self.id_to_individual = id_to_individual
        self.id_to_mating_unit = id_to_mating_unit

    @staticmethod
    def is_valid_family(family):
        """Check if a family is valid."""
        if not family:
            return False
        for parents in family.keys():
            if family[parents].mother.member is None:
                return False
            if family[parents].father.member is None:
                return False
            for children in family[parents].children.individuals:
                if children.member is None:
                    return False
        return True

    def get_graph(self):
        """Build a family graph."""
        graph = nx.Graph()
        for individual_id in self.id_to_individual:
            graph.add_node(individual_id)
        for mating_unit in self.get_mating_units():
            graph.add_edge(
                mating_unit.mother.member.person_id,
                mating_unit.father.member.person_id)
            for child in mating_unit.children_set():
                graph.add_edge(
                    mating_unit.mother.member.person_id, child.member.person_id
                )
                graph.add_edge(
                    mating_unit.father.member.person_id, child.member.person_id
                )
        return graph

    def is_connected(self):
        graph = self.get_graph()
        return nx.is_connected(graph)

    def connected_components(self):
        graph = self.get_graph()
        return nx.connected_components(graph)

    @staticmethod
    def add_missing_members(family):
        """Construct missing family members."""
        new_members = []
        id_to_individual: dict[str, Any] = defaultdict(Individual)

        for member in family.full_members:
            individual = id_to_individual[member.person_id]
            individual.member = member

        missing_father_mothers = {}
        missing_mother_fathers = {}

        for member in family.full_members:
            if member.mom_id == member.dad_id:
                continue
            if member.mom_id is None:
                assert member.dad_id is not None
                if member.dad_id not in missing_mother_fathers:
                    missing_mother_fathers[member.dad_id] = Person(
                        person_id=member.dad_id + ".mother",
                        family_id=family.family_id,
                        mom_id="0",
                        dad_id="0",
                        sex="2",
                        status="-",
                        role=Role.unknown,
                        generated=True,
                    )
                    new_members.append(missing_mother_fathers[member.dad_id])
                member.mom_id = member.dad_id + ".mother"
            elif member.dad_id is None:
                assert member.mom_id is not None
                if member.mom_id not in missing_father_mothers:
                    missing_father_mothers[member.mom_id] = Person(
                        person_id=member.mom_id + ".father",
                        family_id=family.family_id,
                        mom_id="0",
                        dad_id="0",
                        sex="1",
                        status="-",
                        role=Role.unknown,
                        generated=True,
                    )
                    new_members.append(missing_father_mothers[member.mom_id])
                member.dad_id = member.mom_id + ".father"

            mother = id_to_individual[member.mom_id]
            father = id_to_individual[member.dad_id]
            if mother.member is None and mother not in new_members:
                mother.member = Person(
                    person_id=member.mom_id,
                    family_id=family.family_id,
                    mom_id="0",
                    dad_id="0",
                    sex=Sex.F,
                    status=Status.unspecified,
                    role=Role.unknown,
                    generated=True,
                )
                new_members.append(mother.member)
            if father.member is None and father not in new_members:
                father.member = Person(
                    person_id=member.dad_id,
                    family_id=family.family_id,
                    mom_id="0",
                    dad_id="0",
                    sex="1",
                    status="-",
                    role=Role.unknown,
                    generated=True,
                )
                new_members.append(father.member)

        unique_new_members_ids = set([])
        unique_new_members = []
        for person in new_members:
            if person.person_id in unique_new_members_ids:
                continue
            unique_new_members.append(person)
            unique_new_members_ids.add(person.person_id)

        family.add_members(unique_new_members)
        # role_builder = FamilyRoleBuilder(family)
        # role_builder.build_roles()

    @classmethod
    def from_family(cls, family, add_missing_members=True):
        """Build family connections object from a family."""
        assert isinstance(family, Family)

        if add_missing_members:
            cls.add_missing_members(family)

        id_to_individual: dict[str, Any] = defaultdict(Individual)
        id_to_mating_unit = {}

        for member in family.full_members:
            individual = id_to_individual[member.person_id]
            individual.member = member

            if not member.has_both_parents():
                continue

            mother = id_to_individual[member.mom_id]
            father = id_to_individual[member.dad_id]

            mating_unit_key = member.mom_id + "," + member.dad_id
            if mother != father and mating_unit_key not in id_to_mating_unit:
                id_to_mating_unit[mating_unit_key] = MatingUnit(mother, father)

            if mother != father:
                parental_unit = id_to_mating_unit[mating_unit_key]
                individual.parents = parental_unit
                parental_unit.children.individuals.add(individual)

        if cls.is_valid_family(id_to_mating_unit) is False:
            return None

        assert "0" not in id_to_individual
        assert "" not in id_to_individual

        return FamilyConnections(family, id_to_individual, id_to_mating_unit)

    def create_sandwich_instance(self):
        """
        Generate an Interval Graph Sandwich problem instance.

        Based on
        https://academic.oup.com/bioinformatics/article-pdf/17/2/174/442086/170174.pdf
        Slightly modified to support people with multiple mates.
        :return: SandwichInstance
        """
        self.add_ranks()

        individuals = self.get_individuals()
        mating_units = self.get_mating_units()
        sibship_units = self.get_sibship_units()

        all_vertices = individuals | mating_units | sibship_units

        # Ea-: individuals of same rank should not intersect
        same_rank_edges = {
            frozenset([i1, i2])
            for i1 in individuals
            for i2 in individuals
            if i1 is not i2 and i1.rank is i2.rank
        }
        # Allow intersection of individuals who have the same mate. This allows
        # drawing of pedigrees with the curved link when there is a person
        # with more than 2 mates.
        multiple_partners_edges = {
            frozenset([i1, i2])
            for i1 in individuals
            for i2 in [m.other_parent(i1) for m in i1.mating_units]
            if len(i1.mating_units) > 2
        }
        same_rank_edges -= multiple_partners_edges
        same_rank_edges = set(map(tuple, same_rank_edges))  # type: ignore

        # Eb+: mating units and individuals in them should intersect
        mating_edges = {
            (i, m)
            for i in individuals
            for m in mating_units
            if i.individual_set().issubset(m.individual_set())
        }
        # Eb-: and no others of the same rank should intersect
        same_generation_not_mates = {
            (i, m)
            for i in individuals
            for m in mating_units
            if i.generation_ranks() == m.generation_ranks()
        }
        same_generation_not_mates = same_generation_not_mates - mating_edges

        # Ec+: sibship units and individuals in them should intersect
        sibship_edges = {
            (i, s)
            for i in individuals
            for s in sibship_units
            if i.individual_set().issubset(s.individual_set())
        }
        # Ec-: and no others of the same rank should intersect
        same_generation_not_siblings = {
            (i, s)
            for i in individuals
            for s in sibship_units
            if i.parents is not None
            and i.generation_ranks() == s.generation_ranks()
        }
        same_generation_not_siblings = (
            same_generation_not_siblings - sibship_edges
        )

        # Ed+: mating units and corresponding sibships should intersect
        mates_siblings_edges = {
            (m, s)
            for m in mating_units
            for s in sibship_units
            if (m.children.individual_set() is s.individual_set())
        }

        # Ee-: mating units and sibship or mating units of different ranks
        # should not intersect
        intergenerational_edges = {
            (m, a)
            for m in mating_units
            for a in sibship_units | mating_units
            if (m.generation_ranks() & a.generation_ranks() == set())
            and (m.individual_set() & a.individual_set() == set())
            # this check seems redundant
        }
        intergenerational_edges -= mates_siblings_edges

        required_set = mating_edges | sibship_edges | mates_siblings_edges
        forbidden_set = (
            same_rank_edges
            | same_generation_not_mates
            | same_generation_not_siblings
            | intergenerational_edges
        )

        return SandwichInstance.from_sets(
            all_vertices, required_set, forbidden_set
        )

    @property
    def members(self):
        assert self.family is not None
        # for person in self.family.full_members:
        #     yield self.id_to_individual[person.person_id]
        return self.family.full_members

    def add_ranks(self):
        """Calculate and add ranks to the family members."""
        if len(self.id_to_mating_unit) == 0:
            for member in self.id_to_individual.values():
                member.rank = 0
        elif len(self.members) > 0:
            is_rank_set = False
            for member in self.id_to_individual.values():
                if len(member.mating_units) != 0:
                    member.add_rank(0)
                    is_rank_set = True
                    break
            if not is_rank_set:
                list(self.id_to_individual.values())[0].add_rank(0)
            self._fix_ranks()

    def _fix_ranks(self):
        max_rank = self.max_rank()
        for member in self.id_to_individual.values():
            member.rank -= max_rank
            member.rank = -member.rank

    def max_rank(self):
        return reduce(
            lambda acc, i: max(acc, cast(int, i.rank)),
            self.id_to_individual.values(), 0
        )

    def get_individual(self, person_id):
        return self.id_to_individual.get(person_id)

    def get_individuals_with_rank(self, rank):
        return {i for i in self.id_to_individual.values() if i.rank == rank}

    def get_individuals(self):
        return set(self.id_to_individual.values())

    def get_mating_units(self):
        return set(self.id_to_mating_unit.values())

    def get_sibship_units(self):
        return {mu.children for mu in self.id_to_mating_unit.values()}


class IndividualGroup(metaclass=abc.ABCMeta):
    """Group of individuals connected to an individual."""

    @abc.abstractmethod
    def individual_set(self):
        return {}

    def generation_ranks(self):
        return {i.rank for i in self.individual_set()}

    @abc.abstractmethod
    def children_set(self):
        return {}

    def __repr__(self):
        return (
            self.__class__.__name__[0].lower()
            + "{"
            + ",".join(sorted(map(repr, self.individual_set())))
            + "}"
        )

    def __lt__(self, other):
        return repr(self) < repr(other)

    def is_individual(self):
        return False


class Individual(IndividualGroup):
    """Represents an individual and all connected members."""

    NO_RANK = -3673473456

    def __init__(
        self, mating_units=None, member=None, parents=None, rank=NO_RANK
    ):

        if mating_units is None:
            mating_units = []

        self.mating_units = mating_units
        self.member = member
        self.parents = parents
        self.rank = rank

    def individual_set(self):
        return {self}

    def children_set(self):
        return {c for mu in self.mating_units for c in mu.children_set()}

    def add_rank(self, rank):
        """Calculate and set generation rank for each individual in a group."""
        if self.rank != Individual.NO_RANK:
            return

        self.rank = rank

        for mating_unit in self.mating_units:
            for child in mating_unit.children.individuals:
                child.add_rank(rank - 1)

            mating_unit.father.add_rank(rank)
            mating_unit.mother.add_rank(rank)

        if self.parents:
            if self.parents.father:
                self.parents.father.add_rank(rank + 1)
            if self.parents.mother:
                self.parents.mother.add_rank(rank + 1)

    def __repr__(self):
        return str(self.member.person_id)

    def are_siblings(self, other_individual):
        return (
            self.parents is not None
            and self.parents == other_individual.parents
        )

    def are_mates(self, other_individual):
        return (
            len(set(self.mating_units) & set(other_individual.mating_units))
            == 1
        )

    def is_individual(self):
        return True


class SibshipUnit(IndividualGroup):
    """Group of individuals connected as siblings."""

    def __init__(self, individuals=None):
        if individuals is None:
            individuals = set()

        self.individuals = individuals

    def individual_set(self):
        return self.individuals

    def children_set(self):
        return set()


class MatingUnit(IndividualGroup):
    """Gropu of individuals connected in a mating unit."""

    def __init__(self, mother, father, children=None):
        if children is None:
            children = SibshipUnit()

        self.mother = mother
        self.father = father
        self.children = children

        self.mother.mating_units.append(self)
        self.father.mating_units.append(self)

    def individual_set(self):
        return {self.mother, self.father}

    def children_set(self):
        return set(self.children.individuals)

    def other_parent(self, this_parent):
        assert this_parent in (self.mother, self.father)
        if this_parent == self.mother:
            return self.father
        return self.mother
