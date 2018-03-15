import abc
from collections import defaultdict


class PedigreeMember(object):
    def __init__(self, id, family_id, mother, father, sex, effect, label):
        self.id = id
        self.family_id = family_id
        self.mother = mother
        self.father = father
        self.sex = sex
        self.label = label
        self.effect = effect

    def has_known_mother(self):
        return self.mother == '0' or self.mother == ''

    def has_known_father(self):
        return self.father == '0' or self.father == ''

    def has_known_parents(self):
        return self.has_known_father() or self.has_known_mother()


class Pedigree(object):

    def __init__(self, members):
        self.members = members
        self.family_id = members[0].family_id if len(members) > 0 else ""

    def independent_members(self):
        return [m for m in self.members if m.has_known_parents()]


class FamilyConnections(object):

    def __init__(self, pedigree, id_to_individual, id_to_mating_unit):
        self.pedigree = pedigree
        self.id_to_individual = id_to_individual
        self.id_to_mating_unit = id_to_mating_unit

    @staticmethod
    def from_pedigree(pedigree):
        id_to_individual = defaultdict(Individual)
        id_to_mating_unit = {}

        for member in pedigree.members:
            mother = id_to_individual[member.mother]
            father = id_to_individual[member.father]

            mating_unit_key = member.mother + "," + member.father
            if mother != father and not (mating_unit_key in id_to_mating_unit):
                id_to_mating_unit[mating_unit_key] = MatingUnit(mother, father)

            individual = id_to_individual[member.id]
            individual.member = member

            if mother != father:
                parental_unit = id_to_mating_unit[mating_unit_key]
                individual.parents = parental_unit
                parental_unit.children.individuals.add(individual)

        try:
            del id_to_individual["0"]
        except KeyError:
            pass

        try:
            del id_to_individual[""]
        except KeyError:
            pass

        return FamilyConnections(pedigree, id_to_individual, id_to_mating_unit)

    @property
    def members(self):
        if not self.pedigree:
            return []
        return self.pedigree.members

    def add_ranks(self):
        if len(self.members) > 0:
            self.id_to_individual.values()[0].add_rank(0)
            self._fix_ranks()

    def _fix_ranks(self):
        max_rank = self.max_rank()
        for member in self.id_to_individual.values():
            member.rank -= max_rank
            member.rank = -member.rank

    def max_rank(self):
        return reduce(
            lambda acc, i: max(acc, i.rank),
            self.id_to_individual.values(), 0)

    def get_individuals_with_rank(self, rank):
        return {i for i in self.id_to_individual.values() if i.rank == rank}


class IndividualGroup(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def individual_set(self):
        return {}

    def generation_ranks(self):
        return {i.rank for i in self.individual_set()}

    @abc.abstractmethod
    def children_set(self):
        return {}

    def is_individual(self):
        return False

    def __repr__(self):
        return self.__class__.__name__[0].lower() + \
               "{" + ",".join(sorted(map(repr, self.individual_set()))) + "}"


class Individual(IndividualGroup):
    NO_RANK = -3673473456

    def __init__(self, mating_units=None, member=None, parents=None,
                 rank=NO_RANK):

        if mating_units is None:
            mating_units = []

        self.mating_units = mating_units
        self.member = member
        self.parents = parents
        self.rank = rank

    def is_individual(self):
        return True

    def individual_set(self):
        return {self}

    def children_set(self):
        return {c for mu in self.mating_units for c in mu.children_set()}

    def add_rank(self, rank):
        if self.rank != Individual.NO_RANK:
            return

        self.rank = rank

        for mu in self.mating_units:
            for child in mu.children.individuals:
                child.add_rank(rank - 1)

            mu.father.add_rank(rank)
            mu.mother.add_rank(rank)

        if self.parents:
            if self.parents.father:
                self.parents.father.add_rank(rank + 1)
            if self.parents.mother:
                self.parents.mother.add_rank(rank + 1)

    def __repr__(self):
        return str(self.member.id)

    def are_siblings(self, other_individual):
        return (self.parents is not None and
                self.parents == other_individual.parents)

    def are_mates(self, other_individual):
        return len(set(self.mating_units) &
                   set(other_individual.mating_units)) == 1


class SibshipUnit(IndividualGroup):
    def __init__(self, individuals=None):
        if individuals is None:
            individuals = set()

        self.individuals = individuals

    def individual_set(self):
        return self.individuals

    def children_set(self):
        return set()


class MatingUnit(IndividualGroup):

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
        assert this_parent == self.mother or this_parent == self.father
        if this_parent == self.mother:
            return self.father
        return self.mother
