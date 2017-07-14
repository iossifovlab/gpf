import abc
from collections import defaultdict


class PedigreeMember:
    def __init__(self, id, mother, father, gender, label):
        self.id = id
        self.mother = mother
        self.father = father
        self.gender = gender
        self.label = label


class Pedigree:

    def __init__(self, members):
        self.members = members


class IndividualGroup:
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def individual_set(self):
        return {}

    @abc.abstractmethod
    def generation_anks(self):
        return {i.rank for i in self.individual_set()}

    @abc.abstractmethod
    def children_set(self):
        return {}

    @abc.abstractmethod
    def __repr__(self):
        return ",".join(sorted(self.individual_set()))


class Individual(IndividualGroup):
    NO_RANK = -3673473456

    def __init__(self, mating_units=[], member=None, parents=None,
                 rank=NO_RANK):

        self.mating_units = mating_units
        self.member = member
        self.parents = parents
        self.rank = rank

    def individual_set(self):
        return {self}

    def children_set(self):
        return {c for mu in self.mating_units for c in mu.children_set()}

    def add_rank(self, rank):
        if self.rank != Individual.NO_RANK:
            return

        for mu in self.mating_units:
            for c in mu.children_set:
                c.add_rank(rank - 1)

            mu.father.add_rank(rank)
            mu.mother.add_rank(rank)

        if self.parents:
            if self.parents.father:
                self.parents.father.add_rank(rank + 1)
            if self.parents.mother:
                self.parents.mother.add_rank(rank + 1)


class SibshipUnit(IndividualGroup):
    def __init__(self, individuals=set()):
        self.individuals = individuals

    def individual_set(self):
        return self.individuals

    def children_set(self):
        return set()


class MatingUnit(IndividualGroup):

    def __init__(self, mother, father, children=SibshipUnit()):
        self.mother = mother
        self.father = father
        self.children = children

        self.mother.mating_units.push(self)
        self.father.mating_units.push(self)

    def individual_set(self):
        return {self.mother, self.father}

    def children_set(self):
        return set(self.children.individuals)


def createSandwichInstance(pedigree):
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

    del id_to_individual['0']
    del id_to_individual['']

    individuals = set(id_to_individual.values())
    mating_units = set(id_to_mating_unit.values())
    sibship_units = set([mu.children for mu in id_to_mating_unit.values()])

    all_vertices = individuals + mating_units + sibship_units
