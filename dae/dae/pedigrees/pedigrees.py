from __future__ import annotations

import abc

import itertools
import copy
import logging
from collections import deque

from collections import defaultdict
from functools import reduce
from typing import Iterator, Optional, Union, Any, \
    cast, Iterable
import networkx as nx

from dae.variants.attributes import Role, Sex, Status
from dae.pedigrees.family import Person, Family

logger = logging.getLogger(__name__)


class FamilyConnections():
    """Representation of connections between family members."""

    def __init__(
        self, family: Family,
        id_to_individual: dict[str, Individual],
        id_to_mating_unit: dict[str, MatingUnit]
    ) -> None:
        assert family is not None
        assert "0" not in id_to_individual
        assert "" not in id_to_individual

        self.family = family
        self.id_to_individual = id_to_individual
        self.id_to_mating_unit = id_to_mating_unit

    @staticmethod
    def is_valid_family(family: dict[str, MatingUnit]) -> bool:
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

    def get_graph(self) -> nx.Graph:
        """Build a family graph."""
        graph = nx.Graph()
        for individual_id in self.id_to_individual:
            graph.add_node(individual_id)
        for mating_unit in self.get_mating_units():
            assert mating_unit.mother.member is not None
            assert mating_unit.father.member is not None
            graph.add_edge(
                mating_unit.mother.member.person_id,
                mating_unit.father.member.person_id)
            for child in mating_unit.children_set():
                assert child.member is not None
                graph.add_edge(
                    mating_unit.mother.member.person_id, child.member.person_id
                )
                graph.add_edge(
                    mating_unit.father.member.person_id, child.member.person_id
                )
        return graph

    def is_connected(self) -> bool:
        graph = self.get_graph()
        return cast(bool, nx.is_connected(graph))

    def connected_components(self) -> Iterator[nx.Graph]:
        graph = self.get_graph()
        return cast(Iterator[nx.Graph], nx.connected_components(graph))

    @staticmethod
    def add_missing_members(family: Family) -> None:
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
    def from_family(
        cls, family: Family,
        add_missing_members: bool = True
    ) -> Optional[FamilyConnections]:
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

    def create_sandwich_instance(self) -> SandwichInstance:
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

        all_vertices: set[IndividualGroup] = \
            individuals | mating_units | sibship_units

        # Ea-: individuals of same rank should not intersect
        same_rank_edges = {
            (i1, i2)
            for i1 in individuals
            for i2 in individuals
            if i1 is not i2 and i1.rank is i2.rank
        }
        # Allow intersection of individuals who have the same mate. This allows
        # drawing of pedigrees with the curved link when there is a person
        # with more than 2 mates.
        multiple_partners_edges = {
            (i1, i2)
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

        required_set: set[tuple[IndividualGroup, IndividualGroup]] = \
            mating_edges | sibship_edges | mates_siblings_edges
        forbidden_set: set[tuple[IndividualGroup, IndividualGroup]] = \
            same_rank_edges \
            | same_generation_not_mates \
            | same_generation_not_siblings \
            | intergenerational_edges

        return SandwichInstance.from_sets(
            all_vertices, required_set, forbidden_set)

    @property
    def members(self) -> list[Person]:
        assert self.family is not None
        # for person in self.family.full_members:
        #     yield self.id_to_individual[person.person_id]
        return self.family.full_members

    def add_ranks(self) -> None:
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

    def _fix_ranks(self) -> None:
        max_rank = self.max_rank()
        for member in self.id_to_individual.values():
            member.rank -= max_rank
            member.rank = -member.rank

    def max_rank(self) -> int:
        return reduce(
            lambda acc, i: max(acc, i.rank),
            self.id_to_individual.values(), 0
        )

    def get_individual(self, person_id: str) -> Optional[Individual]:
        return self.id_to_individual.get(person_id)

    def get_individuals_with_rank(self, rank: int) -> set[Individual]:
        return {i for i in self.id_to_individual.values() if i.rank == rank}

    def get_individuals(self) -> set[Individual]:
        return set(self.id_to_individual.values())

    def get_mating_units(self) -> set[MatingUnit]:
        return set(self.id_to_mating_unit.values())

    def get_sibship_units(self) -> set[SibshipUnit]:
        return {mu.children for mu in self.id_to_mating_unit.values()}


class IndividualGroup(metaclass=abc.ABCMeta):
    """Group of individuals connected to an individual."""

    @abc.abstractmethod
    def individual_set(self) -> set[Individual]:
        """Return set of individuals in the group."""

    def generation_ranks(self) -> set[int]:
        return {i.rank for i in self.individual_set()}

    @abc.abstractmethod
    def children_set(self) -> set[Individual]:
        """Return set of children in the group."""

    def __repr__(self) -> str:
        return (
            self.__class__.__name__[0].lower()
            + "{"
            + ",".join(sorted(map(repr, self.individual_set())))
            + "}"
        )

    def __lt__(
        self, other: Union[Individual, SibshipUnit, MatingUnit]
    ) -> bool:
        return repr(self) < repr(other)

    def is_individual(self) -> bool:
        return False


class Individual(IndividualGroup):
    """Represents an individual and all connected members."""

    NO_RANK = -3673473456

    def __init__(
        self, mating_units: Optional[list[MatingUnit]] = None,
        member: Optional[Person] = None,
        parents: Optional[MatingUnit] = None,
        rank: int = NO_RANK
    ) -> None:

        if mating_units is None:
            mating_units = []

        self.mating_units = mating_units
        self.member = member
        self.parents = parents
        self.rank = rank

    def individual_set(self) -> set[Individual]:
        return {self}

    def children_set(self) -> set[Individual]:
        return {c for mu in self.mating_units for c in mu.children_set()}

    def add_rank(self, rank: int) -> None:
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

    def __repr__(self) -> str:
        assert self.member is not None
        return str(self.member.person_id)

    def are_siblings(self, other_individual: Individual) -> bool:
        return (
            self.parents is not None
            and self.parents == other_individual.parents
        )

    def are_mates(self, other_individual: Individual) -> bool:
        return (
            len(set(self.mating_units) & set(other_individual.mating_units))
            == 1
        )

    def is_individual(self) -> bool:
        return True


class SibshipUnit(IndividualGroup):
    """Group of individuals connected as siblings."""

    def __init__(
        self, individuals: Optional[Iterable[Individual]] = None
    ) -> None:
        if individuals is None:
            individuals = set()

        self.individuals = set(individuals)

    def individual_set(self) -> set[Individual]:
        return self.individuals

    def children_set(self) -> set[Any]:
        return set()


class MatingUnit(IndividualGroup):
    """Gropu of individuals connected in a mating unit."""

    def __init__(
        self, mother: Individual,
        father: Individual,
        children: Optional[SibshipUnit] = None
    ) -> None:
        if children is None:
            children = SibshipUnit()

        self.mother = mother
        self.father = father
        self.children = children

        self.mother.mating_units.append(self)
        self.father.mating_units.append(self)

    def individual_set(self) -> set[Individual]:
        return {self.mother, self.father}

    def children_set(self) -> set[Individual]:
        return set(self.children.individuals)

    def other_parent(self, this_parent: Individual) -> Individual:
        assert this_parent in (self.mother, self.father)
        if this_parent == self.mother:
            return self.father
        return self.mother


class Interval:
    """Represents an interval between two points on a number line."""

    def __init__(self, left: float = 0.0, right: float = 1.0) -> None:
        """Initialize a new Interval object.

        Args:
            left (float): The left endpoint of the interval. Defaults to 0.0.
            right (float): The right endpoint of the interval. Defaults to 1.0.
        """
        self.left = left
        self.right = right

    def intersection(self, other: IntervalForVertex) -> Optional[Interval]:
        """Compute the intersection of this interval with another interval.

        Args:
            other (IntervalForVertex): The other interval to compute the
                intersection with.

        Returns:
            Optional[Interval]: The intersection interval if it exists,
                None otherwise.
        """
        if self.left < other.right:
            return None
        return Interval(
            max(self.left, other.left), min(self.right, other.right)
        )


class IntervalForVertex(Interval):
    """Represents an interval associated with a vertex in a pedigree."""

    def __init__(
        self, vertex: IndividualGroup,
        left: float = 0.0,
        right: float = 1.0
    ) -> None:
        super().__init__(left, right)
        self.vertex = vertex

    def __repr__(self) -> str:
        return f"i[{self.vertex}> {self.left}:{self.right}]"


class Realization:
    """Represents a realization in a pedigree graph.

    Attributes:
        graph (nx.Graph): The graph representing the pedigree.
        forbidden_graph (nx.Graph): The graph representing forbidden edges
            in the pedigree.
        intervals (Optional[list[IntervalForVertex]]): The intervals for each
            vertex in the pedigree.
        domain (Optional[list[IndividualGroup]]): The domain of the pedigree.
        max_width (int): The maximum width of the pedigree.
        _cached_active_vertices (Optional[set[IndividualGroup]]): Cached set of
            active vertices.
        _cached_maximal_set (Optional[set[IndividualGroup]]): Cached set of
            maximal vertices.
        _graph_neighbors_cache (
            Optional[dict[IndividualGroup, set[IndividualGroup]]]): Cached
            neighbors of each vertex.
        _cached_dangling_set (Optional[set[IndividualGroup]]): Cached set of
            dangling vertices.
        _cached_vertex_degree (Optional[dict[IndividualGroup, int]]): Cached
            degree of each vertex.
    """

    def __init__(
        self,
        graph: nx.Graph,
        forbidden_graph: nx.Graph,
        intervals: Optional[list[IntervalForVertex]] = None,
        domain: Optional[list[IndividualGroup]] = None,
        max_width: int = 3,
        _cached_active_vertices: Optional[set[IndividualGroup]] = None,
        _cached_maximal_set: Optional[set[IndividualGroup]] = None,
        _graph_neighbors_cache: Optional[
            dict[IndividualGroup, set[IndividualGroup]]] = None,
        _cached_dangling_set: Optional[set[IndividualGroup]] = None,
        _cached_vertex_degree: Optional[dict[IndividualGroup, int]] = None,
    ) -> None:
        if domain is None:
            domain = []
        if intervals is None:
            intervals = []
        self.graph = graph
        self.forbidden_graph = forbidden_graph
        self.intervals = intervals
        self.domain = domain
        self.max_width = max_width

        self._domain_set = set(self.domain)
        self._cached_active_vertices: Optional[set[IndividualGroup]] = \
            _cached_active_vertices
        self._cached_maximal_set = _cached_maximal_set
        self._cached_dangling_set = _cached_dangling_set

        if _cached_vertex_degree is None:
            _cached_vertex_degree = {}

        self._cached_vertex_degree = _cached_vertex_degree

        if _graph_neighbors_cache is None:
            # print("_graph_neighbors_cache recomputed")
            _graph_neighbors_cache = {
                v: set(self.graph.neighbors(v)) for v in self.graph.nodes()
            }

        self._graph_neighbors_cache = _graph_neighbors_cache

    def copy(self) -> Realization:
        return Realization(
            self.graph,
            self.forbidden_graph,
            list(map(copy.copy, self.intervals)),  # type: ignore
            copy.copy(self.domain),
            self.max_width,
            self._cached_active_vertices,
            self._cached_maximal_set,
            self._graph_neighbors_cache,
            self._cached_dangling_set,
            self._cached_vertex_degree,
        )

    def __repr__(self) -> str:
        ordered_domain = sorted(repr(v) for v in self.domain)
        return ";".join(ordered_domain)

    def extend(self, vertex: IndividualGroup) -> bool:
        if not self.can_extend(vertex):
            return False

        self.force_extend(vertex)

        return True

    def force_extend(self, vertex: IndividualGroup) -> None:
        """Extend the pedigree by adding a new vertex.

        Parameters:
        - vertex (IndividualGroup): The vertex to be added to the pedigree.

        Returns:
        - None
        """
        max_right = next(
            self.get_interval(v).right for v in self.get_maximal_set()
        )

        p = 0.5 + max_right

        for active_vertex in self.get_active_vertices():
            interval = self.get_interval(active_vertex)
            interval.right = p + 1

        self.domain.append(vertex)
        self.intervals.append(IntervalForVertex(vertex, p, p + 1))

        self._domain_set.add(vertex)
        self._cached_active_vertices = None
        self._cached_maximal_set = None
        self._cached_dangling_set = None
        self._cached_vertex_degree = {}

    def can_extend(
            self, new_vertex: IndividualGroup
    ) -> bool:
        """Determine whether a new vertex can be added to the pedigree.

        Args:
            new_vertex (IndividualGroup): The new vertex to be added.

        Returns:
            bool: True if the new vertex can be added, False otherwise.
        """
        temp_realization = Realization(
            self.graph,
            self.forbidden_graph,
            self.intervals + [IntervalForVertex(new_vertex)],
            self.domain + [new_vertex],
            _graph_neighbors_cache=self._graph_neighbors_cache,
        )

        if self._has_forbidden_edge(new_vertex):
            # print("_has_forbidden_edge!")
            return False

        if self._is_active_bounded(temp_realization, new_vertex):
            return False

        # pylint: disable=protected-access
        if temp_realization._exceeds_max_width():
            # print("max width reached!")
            return False

        if not self._old_dangling_same(new_vertex, temp_realization):
            # print("_old_dangling_same!")
            return False

        if not self._new_dangling_valid(new_vertex, temp_realization):
            # print("_new_dangling_valid!")
            return False

        if not self._new_active_valid(new_vertex, temp_realization):
            # print("_new_active_valid!")
            return False

        assert self.get_active_vertices().issubset(self.get_maximal_set())

        return True

    def _is_active_bounded(
        self, new_realization: Realization,
        new_vertex: IndividualGroup
    ) -> bool:
        if len(self.get_active_vertices()) == self.max_width - 1:
            if new_vertex not in self.dangling_set():
                return True

        active_vertices = self.get_active_vertices().intersection(
            new_realization.get_active_vertices()
        )
        for active in active_vertices:
            if new_realization.degree(active) != self.degree(active) + 1:
                return True

        return False

    def _exceeds_max_width(self) -> bool:
        return len(self.get_active_vertices()) >= self.max_width

    def _has_forbidden_edge(self, new_vertex: IndividualGroup) -> bool:
        forbidden = set(self.forbidden_graph.neighbors(new_vertex))
        active_vertices = self.get_active_vertices()

        return forbidden & active_vertices != set()

    def _new_active_valid(
        self, new_vertex: IndividualGroup,
        new_realization: Realization
    ) -> bool:
        new_active = new_realization.get_active_vertices()
        old_active_and_new_vertex = self.get_active_vertices() | {new_vertex}
        expected_new_active = {
            v
            for v in old_active_and_new_vertex
            if len(new_realization.dangling(v)) != 0
        }

        return new_active == expected_new_active

    def _new_dangling_valid(
        self, new_vertex: IndividualGroup,
        new_realization: Realization
    ) -> bool:
        new_dangling = new_realization.dangling(new_vertex)
        new_edges = (
            set(self.graph.neighbors(new_vertex)) - self.get_active_vertices()
        )
        return new_dangling == new_edges

    def _old_dangling_same(
        self, new_vertex: IndividualGroup,
        new_realization: Realization
    ) -> bool:
        for active_vertex in self.get_active_vertices():
            dangling = self.dangling(active_vertex)
            new_dangling = new_realization.dangling(active_vertex)
            dangling -= {new_vertex}

            if new_dangling != dangling:
                return False

        return True

    def get_interval(
        self, vertex: IndividualGroup
    ) -> IntervalForVertex:
        index = self.domain.index(vertex)

        return self.intervals[index]

    def is_in_interval_order(self, v1_idx: int, v2_idx: int) -> bool:
        interval1 = self.intervals[v1_idx]
        interval2 = self.intervals[v2_idx]

        return interval1.right < interval2.left

    def is_maximal(self, index: int) -> bool:
        for i, _ in enumerate(self.domain):
            if i != index and self.is_in_interval_order(index, i):
                return False

        return True

    def get_maximal_set(self) -> set[IndividualGroup]:
        """Return the maximal set of IndividualGroup objects in the domain.

        If the maximal set has already been computed, it is returned from the
        cache. Otherwise, the maximal set is computed by iterating over the
        domain and checking if each IndividualGroup is maximal. The computed
        maximal set is then stored in the cache for future use.

        Returns:
            set[IndividualGroup]: The maximal set of IndividualGroup objects.
        """
        if self._cached_maximal_set:
            return self._cached_maximal_set

        self._cached_maximal_set = {
            v for i, v in enumerate(self.domain) if self.is_maximal(i)
        }

        return self._cached_maximal_set

    def get_active_vertex_edges(
        self, vertex: IndividualGroup
    ) -> set[IndividualGroup]:
        return self._graph_neighbors_cache[vertex].difference(self._domain_set)

    def is_active_vertex(self, vertex: IndividualGroup) -> bool:
        neighbors = self._graph_neighbors_cache[vertex]
        for v in neighbors:
            if v not in self._domain_set:
                return True
        return False

    def get_active_vertices(self) -> set[IndividualGroup]:
        """Return a set of active vertices in the domain.

        Returns:
            set[IndividualGroup]: A set of active vertices.
        """
        if self._cached_active_vertices:
            return self._cached_active_vertices
        self._cached_active_vertices = set()
        for v in self.domain:
            if self.is_active_vertex(v):
                self._cached_active_vertices.add(v)
        return self._cached_active_vertices

    def dangling(
        self, vertex: IndividualGroup
    ) -> set[IndividualGroup]:
        return self.get_active_vertex_edges(vertex)

    def dangling_set(self) -> set[IndividualGroup]:
        """Return a set of the dangling vertices in the pedigree graph.

        Dangling vertices are vertices that have no outgoing edges.

        Returns:
            set[IndividualGroup]: A set of IndividualGroup objects representing
            the dangling vertices.
        """
        if self._cached_dangling_set:
            return self._cached_dangling_set

        self._cached_dangling_set = set(
            v
            for active in self.get_active_vertices()
            for v in self.dangling(active)
        )

        return self._cached_dangling_set

    def degree(self, vertex: IndividualGroup) -> int:
        """Calculate the degree of a vertex in the pedigree.

        Parameters:
            vertex (IndividualGroup): The vertex for which to calculate
            the degree.

        Returns:
            int: The degree of the vertex.
        """
        if vertex in self._cached_vertex_degree:
            return self._cached_vertex_degree[vertex]

        v_interval = self.get_interval(vertex)
        result = (
            len(
                [
                    1
                    for i in self.intervals
                    if v_interval.intersection(i) is not None
                ]
            )
            - 1
        )

        self._cached_vertex_degree[vertex] = result

        return result


class SandwichInstance:
    """Represent a sandwich instance representing the pedigree.

    Attributes:
        vertices (set[IndividualGroup]): The set of vertices in the sandwich
            instance.
        required_graph (nx.Graph): The required graph representing the
            connections between vertices.
        forbidden_graph (nx.Graph): The forbidden graph representing the
            forbidden connections between vertices.
    """

    def __init__(
        self, vertices: set[IndividualGroup],
        required_graph: nx.Graph,
        forbidden_graph: nx.Graph
    ) -> None:
        self.vertices = vertices
        self.required_graph = required_graph
        self.forbidden_graph = forbidden_graph

    @staticmethod
    def from_sets(
        all_vertices: set[IndividualGroup],
        required_set: set[tuple[IndividualGroup, IndividualGroup]],
        forbidden_set: set[tuple[IndividualGroup, IndividualGroup]]
    ) -> SandwichInstance:
        """Create a SandwichInstance object.

        Args:
            all_vertices (set[IndividualGroup]): Set of all vertices in the
                graph.
            required_set (set[tuple[IndividualGroup, IndividualGroup]]): Set
                of required edges.
            forbidden_set (set[tuple[IndividualGroup, IndividualGroup]]): Set
                of forbidden edges.

        Returns:
            SandwichInstance: The created SandwichInstance object.
        """
        required_graph = nx.Graph()
        required_graph.add_nodes_from(all_vertices)
        required_graph.add_edges_from(required_set)

        forbidden_graph = nx.Graph()
        forbidden_graph.add_nodes_from(all_vertices)
        forbidden_graph.add_edges_from(forbidden_set)

        return SandwichInstance(all_vertices, required_graph, forbidden_graph)


def copy_graph(graph: nx.Graph) -> nx.Graph:
    result = nx.Graph()
    result.add_nodes_from(graph.nodes())
    result.add_edges_from(graph.edges())
    return result


class SandwichSolver:
    """A class that provides methods for solving sandwich instances.

    Methods:
    - solve(sandwich_instance: SandwichInstance):
        Solves the given sandwich instance and returns a list of intervals for
        each vertex, or None if no solution is found.
    - try_solve(sandwich_instance: SandwichInstance)
        Tries to solve the given sandwich instance and returns a list of
        intervals for each vertex, or None if no solution is found.
    """

    @staticmethod
    def solve(
        sandwich_instance: SandwichInstance
    ) -> Optional[list[IntervalForVertex]]:
        """Solve the sandwich instance.

        Args:
            sandwich_instance (SandwichInstance): The sandwich instance to
            solve.

        Returns:
            Optional[list[IntervalForVertex]]: A list of intervals for each
            vertex if a solution is found, otherwise an empty list.
        """
        forbidden_graph = sandwich_instance.forbidden_graph

        if len(sandwich_instance.required_graph.edges()) == 0:
            return SandwichSolver.try_solve(sandwich_instance)
        logger.debug(
            "sandwich forbidden graph edges: %s; %s",
            len(forbidden_graph.edges()),
            forbidden_graph.edges(),
        )

        for count in range(0, len(forbidden_graph.edges())):
            for edges_to_remove in itertools.combinations(
                    sorted(forbidden_graph.edges()), count):

                logger.debug("trying to remove edges: %s", edges_to_remove)
                # if count == 2:
                #     return

                # print(("removing", edges_to_remove))

                current_forbidden_graph = copy_graph(forbidden_graph)
                current_forbidden_graph.remove_edges_from(edges_to_remove)

                current_instance = SandwichInstance(
                    sandwich_instance.vertices,
                    sandwich_instance.required_graph,
                    current_forbidden_graph,
                )

                result = SandwichSolver.try_solve(current_instance)

                if result:
                    # print(("removed:", count))  # , edges_to_remove)
                    return result
        return []

    @staticmethod
    def try_solve(
        sandwich_instance: SandwichInstance
    ) -> Optional[list[IntervalForVertex]]:
        """Try to solve the sandwich instance by finding a realization.

        Searchs for realization that satisfies the given constraints.

        Args:
            sandwich_instance (SandwichInstance): The sandwich instance to be
            solved.

        Returns:
            Optional[list[IntervalForVertex]]: A list of intervals for each
            vertex if a solution is found,otherwise None.
        """
        initial_realization: list[Realization] = []
        current_iteration = 0

        for i, vertex in enumerate(sandwich_instance.vertices):
            # pylint: disable=protected-access
            initial_realization.append(
                Realization(
                    sandwich_instance.required_graph,
                    sandwich_instance.forbidden_graph,
                    [IntervalForVertex(vertex)],
                    [vertex],
                    _graph_neighbors_cache=initial_realization[
                        0
                    ]._graph_neighbors_cache
                    if i > 0
                    else None,
                )
            )

        realizations_queue = deque(sorted(initial_realization, key=str))

        visited_realizations = set()

        vertices_length = len(sandwich_instance.vertices)

        if vertices_length == 1:
            realization = realizations_queue.pop()
            return realization.intervals

        while len(realizations_queue) > 0:
            realization = realizations_queue.pop()
            current_iteration += 1

            if current_iteration == 100000:
                logger.warning(
                    "bailing at %s iterations...", current_iteration
                )
                return None

            other_vertices = sandwich_instance.vertices.difference(
                realization.domain
            )

            # other_vertices = sorted(other_vertices, key=str)
            can_extend_f = realization.can_extend

            for vertex in other_vertices:

                can_extend = can_extend_f(vertex)

                if not can_extend:
                    continue

                cloned_realization = realization.copy()
                cloned_realization.force_extend(vertex)

                if len(cloned_realization.domain) == vertices_length:
                    logger.debug(
                        "sandwitch iterations count: %s", current_iteration
                    )
                    return cloned_realization.intervals
                domain_string = repr(cloned_realization)
                if domain_string not in visited_realizations:
                    visited_realizations.add(domain_string)
                    realizations_queue.append(cloned_realization)

        return None
