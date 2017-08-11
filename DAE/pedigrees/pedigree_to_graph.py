#!/usr/bin/env python2.7

import abc
from collections import defaultdict
import argparse
import csv
from functools import reduce

from interval_sandwich import SandwichInstance, SandwichSolver
from layout import Layout
from drawing import PDFLayoutDrawer, OffsetLayoutDrawer


class CsvPedigreeReader:

    def read_file(self, file):
        families = {}
        reader = csv.DictReader(file)
        for row in reader:
            kwargs = {
                "family_id": row["family_id"],
                "id": row["Person"],
                "father": row["Father"],
                "mother": row["Mother"],
                "sex": row["Sex"],
                "label": "",
                "effect": row["Scored Affected Status"],
            }
            member = PedigreeMember(**kwargs)
            if member.family_id not in families:
                families[member.family_id] = Pedigree([member])

            families[member.family_id].members.append(member)

        return families.values()


class PedigreeMember:
    def __init__(self, id, family_id, mother, father, sex, effect, label):
        self.id = id
        self.family_id = family_id
        self.mother = mother
        self.father = father
        self.sex = sex
        self.label = label


class Pedigree:

    def __init__(self, members):
        self.members = members
        self.family_id = members[0].family_id if len(members) > 0 else ""

    def create_sandwich_instance(self):
        id_to_individual = defaultdict(Individual)
        id_to_mating_unit = {}

        for member in self.members:
            mother = id_to_individual[member.mother]
            father = id_to_individual[member.father]

            mating_unit_key = member.mother + "," + member.father
            # print("key", mating_unit_key)
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

        individuals = set(id_to_individual.values())
        mating_units = set(id_to_mating_unit.values())
        sibship_units = set([mu.children for mu in id_to_mating_unit.values()])

        all_vertices = individuals | mating_units | sibship_units

        if len(individuals) != 0:
            individuals.__iter__().next().add_rank(0)
            self._fix_rank(individuals)

        # Ea-
        same_rank_edges = {frozenset([i1, i2])
                           for i1 in individuals for i2 in individuals
                           if i1 is not i2 and i1.rank is i2.rank}
        same_rank_edges = set(map(tuple, same_rank_edges))

        # Eb+
        mating_edges = {(i, m) for i in individuals for m in mating_units
                        if i.individual_set().issubset(m.individual_set())}
        # Eb-
        same_generation_not_mates = \
            {(i, m) for i in individuals for m in mating_units
             if i.generation_ranks() == m.generation_ranks()}
        same_generation_not_mates = same_generation_not_mates - mating_edges

        # Ec+
        sibship_edges = {(i, s) for i in individuals for s in sibship_units
                         if i.individual_set().issubset(s.individual_set())}
        # Ec-
        same_generation_not_siblings = \
            {(i, s) for i in individuals for s in sibship_units
             if i.generation_ranks() == s.generation_ranks()}
        same_generation_not_siblings = same_generation_not_siblings \
            - sibship_edges

        # Ed+
        mates_siblings_edges = {(m, s) for m in mating_units
                                for s in sibship_units
                                if(m.children.individual_set() is
                                    s.individual_set())}

        # Ee-
        intergenerational_edges = \
            {(m, a) for m in mating_units for a in sibship_units | mating_units
             if (m.generation_ranks() & a.generation_ranks() == set()) and
             (m.individual_set() & a.individual_set() == set())}
        intergenerational_edges -= mates_siblings_edges

        required_set = mating_edges | sibship_edges | mates_siblings_edges
        forbidden_set = same_rank_edges | same_generation_not_mates \
            | same_generation_not_siblings | intergenerational_edges

        # print("all vertices", len(all_vertices), all_vertices)
        # print("required edges", len(required_set), required_set)
        # print("forbidden edges", len(forbidden_set), forbidden_set)

        return SandwichInstance.from_sets(
            all_vertices, required_set, forbidden_set)

    def _fix_rank(self, individuals):
        max_rank = reduce(lambda acc, i: max(acc, i.rank), individuals, 0)
        for individual in individuals:
            individual.rank -= max_rank
            individual.rank = -individual.rank


class IndividualGroup:
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def individual_set(self):
        return {}

    def generation_ranks(self):
        return {i.rank for i in self.individual_set()}

    @abc.abstractmethod
    def children_set(self):
        return {}

    def __repr__(self):
        return "{" + ",".join(sorted(map(repr, self.individual_set()))) + "}"


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


def main():
    parser = argparse.ArgumentParser(description="Draw PDP.")
    parser.add_argument("file", metavar="f", type=argparse.FileType("r"),
                        help="the .ped file")

    args = parser.parse_args()
    pedigrees = CsvPedigreeReader().read_file(args.file)

    pdf_drawer = PDFLayoutDrawer("first.pdf")

    for family in sorted(pedigrees, key=lambda x: x.family_id):
        # if family.family_id == "AU0052":
        sandwich_instance = family.create_sandwich_instance()
        intervals = SandwichSolver.solve(sandwich_instance)
        # print(intervals)
        if intervals is None:
            print(family.family_id)
            print("No intervals")
        if intervals:
            # print("intervals", intervals)
            individuals_intervals = filter(
                lambda interval: isinstance(interval.vertex, Individual),
                intervals
            )
            mating_units = {mu for i in individuals_intervals
                            for mu in i.vertex.mating_units}
            if len(mating_units) > 1:
                print(family.family_id)
                layout = Layout(individuals_intervals)
                layout_drawer = OffsetLayoutDrawer(layout, 0, 0)
                pdf_drawer.add_page(layout_drawer.draw(), family.family_id)

    pdf_drawer.save_file()


if __name__ == "__main__":
    main()
