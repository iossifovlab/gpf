#!/usr/bin/env python
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals
from builtins import str
from builtins import map
from builtins import object
import abc
from collections import defaultdict
import argparse
from functools import reduce
import pandas as pd

from pedigrees.interval_sandwich import SandwichInstance
from future.utils import with_metaclass
from variants.attributes import Role, Sex


class PedigreeMember(object):
    def __init__(self, id, family_id, mother, father, sex, status, role,
                 layout=None, generated=False):
        self.id = id
        self.family_id = family_id
        self.mother = mother
        self.father = father
        self.sex = sex
        self.status = status
        self.layout = layout
        self.role = Role.from_name(role)
        self.generated = generated

    def has_known_mother(self):
        return self.mother == '0' or self.mother == ''

    def has_known_father(self):
        return self.father == '0' or self.father == ''

    def has_known_parents(self):
        return self.has_known_father() or self.has_known_mother()

    def get_member_dataframe(self):
        phenotype = "unknown"
        if self.status == "1":
            phenotype = "unaffected"
        elif self.status == "2":
            phenotype = "affected"
        return pd.DataFrame.from_dict({
            "family_id": [self.family_id],
            "person_id": [self.id],
            "sample_id": [self.id],
            "sex": [Sex.from_name_or_value(self.sex)],
            "role": [self.role],
            "status": [self.status],
            "mom_id": [self.mother],
            "dad_id": [self.father],
            "layout": [self.layout],
            "generated": [self.generated],
            "phenotype": [phenotype]
        })


class Pedigree(object):

    def __init__(self, members):
        self._members = members
        self.family_id = members[0].family_id if len(members) > 0 else ""
        self._independent_members = None

    @property
    def members(self):
        return self._members

    def add_members(self, new_members):
        self._members += new_members

    def add_member(self, member):
        self._members.append(member)
        self._independent_members = None

    def independent_members(self):
        if not self._independent_members:
            self._independent_members = \
                [m for m in self._members if m.has_known_parents()]

        return self._independent_members

    def get_pedigree_dataframe(self):
        return pd.concat([member.get_member_dataframe()
                          for member in self._members])


class FamilyConnections(object):

    def __init__(self, pedigree, id_to_individual, id_to_mating_unit):
        self.pedigree = pedigree
        self.id_to_individual = id_to_individual
        self.id_to_mating_unit = id_to_mating_unit

    @staticmethod
    def is_valid_family(family):
        for parents in family.keys():
            if family[parents].mother.member is None:
                return False
            if family[parents].father.member is None:
                return False
            for children in family[parents].children.individuals:
                if children.member is None:
                    return False
        return True

    @staticmethod
    def add_missing_members(pedigree):
        new_members = []
        id_to_individual = defaultdict(Individual)

        for member in pedigree.members:
            individual = id_to_individual[member.id]
            individual.member = member

        missing_father_mothers = {}
        missing_mother_fathers = {}

        for member in pedigree.members:
            if member.mother == member.father:
                continue
            if member.mother == "0":
                if member.father not in missing_mother_fathers:
                    missing_mother_fathers[member.father] = PedigreeMember(
                        member.father + ".mother", pedigree.family_id,
                        "0", "0", "2", "-", Role.mom, generated=True)
                    new_members.append(missing_mother_fathers[member.father])
                member.mother = member.father + ".mother"
            elif member.father == "0":
                if member.mother not in missing_father_mothers:
                    missing_father_mothers[member.mother] = PedigreeMember(
                        member.mother + ".father", pedigree.family_id,
                        "0", "0", "1", "-", Role.dad, generated=True)
                    new_members.append(missing_father_mothers[member.mother])
                member.father = member.mother + ".father"

            mother = id_to_individual[member.mother]
            father = id_to_individual[member.father]
            if mother.member is None and mother not in new_members:
                mother.member = PedigreeMember(
                    member.mother, pedigree.family_id, "0", "0", "2", "-",
                    Role.mom, generated=True)
                new_members.append(mother.member)
            if father.member is None and father not in new_members:
                father.member = PedigreeMember(
                    member.father, pedigree.family_id, "0", "0", "1", "-",
                    Role.dad, generated=True)
                new_members.append(father.member)

        pedigree.add_members(new_members)

    @classmethod
    def from_pedigree(cls, pedigree, add_missing_members=True):
        if add_missing_members:
            cls.add_missing_members(pedigree)

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

        if cls.is_valid_family(id_to_mating_unit) is False:
            return None

        try:
            del id_to_individual["0"]
        except KeyError:
            pass

        try:
            del id_to_individual[""]
        except KeyError:
            pass

        return FamilyConnections(pedigree, id_to_individual, id_to_mating_unit)

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
        same_rank_edges = set(map(tuple, same_rank_edges))

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
            if i.parents is not None and
            i.generation_ranks() == s.generation_ranks()
        }
        same_generation_not_siblings = same_generation_not_siblings \
            - sibship_edges

        # Ed+: mating units and corresponding sibships should intersect
        mates_siblings_edges = {
            (m, s)
            for m in mating_units
            for s in sibship_units
            if(m.children.individual_set() is
                s.individual_set())
        }

        # Ee-: mating units and sibship or mating units of different ranks
        # should not intersect
        intergenerational_edges = {
            (m, a)
            for m in mating_units
            for a in sibship_units | mating_units
            if (m.generation_ranks() & a.generation_ranks() == set()) and
            (m.individual_set() & a.individual_set() == set())
            # this check seems redundant
        }
        intergenerational_edges -= mates_siblings_edges

        required_set = mating_edges | sibship_edges | mates_siblings_edges
        forbidden_set = same_rank_edges | same_generation_not_mates \
            | same_generation_not_siblings | intergenerational_edges

        # print("same_rank_edges", len(same_rank_edges), same_rank_edges)
        # print("same_generation_not_mates",
        #       len(same_generation_not_mates), same_generation_not_mates)
        # print("same_generation_not_siblings",
        #       len(same_generation_not_siblings), same_generation_not_siblings)
        # print("intergenerational_edges",
        #       len(intergenerational_edges), intergenerational_edges)

        # print("all vertices", len(all_vertices), all_vertices)
        # print("required edges", len(required_set), required_set)
        # print("forbidden edges", len(forbidden_set), forbidden_set)

        return SandwichInstance.from_sets(
            all_vertices, required_set, forbidden_set)

    @property
    def members(self):
        if not self.pedigree:
            return []
        return self.pedigree.members

    def add_ranks(self):
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
            lambda acc, i: max(acc, i.rank),
            self.id_to_individual.values(), 0)

    def get_individuals_with_rank(self, rank):
        return {i for i in self.id_to_individual.values() if i.rank == rank}

    def get_individuals(self):
        return set(self.id_to_individual.values())

    def get_mating_units(self):
        return set(self.id_to_mating_unit.values())

    def get_sibship_units(self):
        return set([mu.children
                    for mu in list(self.id_to_mating_unit.values())])


class IndividualGroup(with_metaclass(abc.ABCMeta, object)):
    @abc.abstractmethod
    def individual_set(self):
        return {}

    def generation_ranks(self):
        return {i.rank for i in self.individual_set()}

    @abc.abstractmethod
    def children_set(self):
        return {}

    def __repr__(self):
        return\
            self.__class__.__name__[0].lower() + \
            "{" + ",".join(sorted(map(repr, self.individual_set()))) + "}"

    def __lt__(self, other):
        return repr(self) < repr(other)

    def is_individual(self):
        return False


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

    def is_individual(self):
        return True


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


def get_argument_parser(description):
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "file", metavar="f", help="the .ped file")
    parser.add_argument(
        "--output", metavar="o", help="the output filename file",
        default="output.pdf")
    parser.add_argument(
        "--layout-column", metavar="l", default="layout",
        help="layout column name to be used when saving the layout. "
        "Default to layout.")
    parser.add_argument(
        "--generated-column", metavar="m", default="generated",
        help="generated column name to be used when generate person")
    parser.add_argument(
        '--delimiter', help='delimiter used in the split column; defaults to '
        '"\\t"', default='\t', action='store')
    parser.add_argument(
        '--family_id', help='Specify family id column label. Default to '
        'familyId.', default='familyId', action='store')
    parser.add_argument(
        '--id', help='Specify id column label. Default to personId.',
        default='personId', action='store')
    parser.add_argument(
        '--father', help='Specify father column label. Default to dadId.',
        default='dadId', action='store')
    parser.add_argument(
        '--mother', help='Specify mother column label. Default to momId.',
        default='momId', action='store')
    parser.add_argument(
        '--sex', help='Specify sex column label. Default to gender.',
        default='gender', action='store')
    parser.add_argument(
        '--status', help='Specify status column label. Default to status.',
        default='status', action='store')
    parser.add_argument(
        '--role', help='Specify role column label. Default to role.',
        default='role', action='store')
    parser.add_argument(
        '--no-header-order', help='Comma separated order of columns in header '
        'when header is not in the input file. Values for columns are '
        'familyId, personId, dadId, momId, gender, status. You can replace '
        'unnecessary column with `_`.', dest='no_header_order', default=None,
        action='store')
    parser.add_argument(
        '--processes', type=int, default=4, dest='processes',
        help='Number of processes', action='store'
    )

    return parser
