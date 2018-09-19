#!/usr/bin/env python2.7
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals
from builtins import str
from builtins import map
from builtins import object
import abc
from collections import defaultdict
import argparse
import csv
import collections

from tools.interval_sandwich import SandwichInstance, SandwichSolver
from tools.layout import Layout
from tools.drawing import PDFLayoutDrawer, OffsetLayoutDrawer
from future.utils import with_metaclass


class CsvPedigreeReader(object):

    def read_file(self, file, columns_labels={}, header=None, delimiter='\t'):
        if not columns_labels:
            columns_labels = CsvPedigreeReader.get_column_labels
        families = {}
        with open(file) as csvfile:
            reader = csv.DictReader(csvfile, fieldnames=header,
                                    delimiter=delimiter.encode('utf-8'))
            for row in reader:
                kwargs = {
                    "family_id": row[columns_labels["family_id"]],
                    "id": row[columns_labels["id"]],
                    "father": row[columns_labels["father"]],
                    "mother": row[columns_labels["mother"]],
                    "sex": row[columns_labels["sex"]],
                    "label": "",
                    "effect": row[columns_labels["effect"]],
                }
                member = PedigreeMember(**kwargs)
                if member.family_id not in families:
                    families[member.family_id] = Pedigree([member])
                else:
                    families[member.family_id].members.append(member)

        return list(families.values())

    @staticmethod
    def get_column_labels():
        return {
            "family_id": "familyId",
            "id": "personId",
            "father": "dadId",
            "mother": "momId",
            "sex": "gender",
            "label": "",
            "effect": "status"
        }


class PedigreeMember(object):
    def __init__(self, id, family_id, mother, father, sex, effect, label):
        self.id = id
        self.family_id = family_id
        self.mother = mother
        self.father = father
        self.sex = sex
        self.label = label


class Pedigree(object):

    def __init__(self, members):
        self.members = members
        self.family_id = members[0].family_id if len(members) > 0 else ""

    def validate_family(self, family):
        for parents in family.keys():
            if family[parents].mother.member is None:
                return False
            if family[parents].father.member is None:
                return False
            for children in family[parents].children.individuals:
                if children.member is None:
                    return False
        return True

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

        if self.validate_family(id_to_mating_unit) is False:
            return None

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
        sibship_units = set([mu.children for mu in list(id_to_mating_unit.values())])

        all_vertices = individuals | mating_units | sibship_units

        if len(individuals) != 0:
            individuals.__iter__().next().add_rank(0)
            Pedigree._fix_rank(individuals)

        # Ea-
        same_rank_edges = {frozenset([i1, i2])
                           for i1 in individuals for i2 in individuals
                           if i1 is not i2 and i1.rank is i2.rank}
        multiple_partners_edges = {
            frozenset([i1, i2])
            for i1 in individuals
            for i2 in [m.other_parent(i1) for m in i1.mating_units]
            if len(i1.mating_units) > 2
        }
        same_rank_edges -= multiple_partners_edges
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
             if i.parents is not None and
                i.generation_ranks() == s.generation_ranks()}
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

    @staticmethod
    def _fix_rank(individuals):
        max_rank = reduce(lambda acc, i: max(acc, i.rank), individuals, 0)
        for individual in individuals:
            individual.rank -= max_rank
            individual.rank = -individual.rank


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

    def is_individual(self):
        return False


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

    def is_individual(self):
        return False


class LayoutSaver(object):

    def __init__(self, input_filename, output_filename,
            fieldname="person_coordinates"):
        self.input_filename = input_filename
        self.output_filename = output_filename
        self.fieldname = fieldname
        self._people_with_layout = collections.OrderedDict()

    @staticmethod
    def _member_key(family_id, individual_id):
        return "{};{}".format(family_id, individual_id)

    def writerow(self, family, layout):
        for individual_id, position in list(layout.id_to_position.items()):
            row = {
                self.fieldname: "{},{}".format(position.x, position.y)
            }

            key = self._member_key(family.family_id, individual_id)

            self._people_with_layout[key] = row

    def save(self):
        with open(self.input_filename, "r") as input_file, \
                open(self.output_filename, "w") as output_file:

            reader = csv.DictReader(input_file, delimiter="\t")
            fieldnames = list(reader.fieldnames)

            assert self.fieldname not in fieldnames, \
                "{} already in file {}".format(
                    self.fieldname, self.input_filename)

            writer = csv.DictWriter(
                output_file, reader.fieldnames + [self.fieldname],
                delimiter='\t')

            writer.writeheader()

            for row in reader:
                row_copy = row.copy()

                key = self._member_key(row['familyId'], row['personId'])

                if key in self._people_with_layout:
                    row_copy.update(self._people_with_layout[key])
                else:
                    row_copy[self.fieldname] = ""

                writer.writerow(row_copy)


def main():
    parser = argparse.ArgumentParser(description="Draw PDP.")
    parser.add_argument(
        "file", metavar="f", help="the .ped file")
    parser.add_argument(
        "--output", metavar="o", help="the output filename file",
        default="output.pdf")
    parser.add_argument(
        "--save-layout", metavar="o",
        help="save the layout with pedigree info ")
    parser.add_argument(
        "--layout-column", metavar="l", default="layoutCoords",
        help="layout column name to be used when saving the layout")
    parser.add_argument(
        '--no-header', help='no header in the input file',
        default=None, action='store_true', dest='no_header')
    parser.add_argument(
        '--delimiter', help='delimiter used in the split column; defaults to '
        '"\\t"', default='\t', action='store')
    parser.add_argument(
        '--column', help='Add column names. Possible columns with there '
        'default values are family_id:familyId, id:personId, father:dadId, '
        'mother:momId, sex:gender, label:, effect:status. If value is int it '
        'is 0 position.', dest='columns', action='append',
        metavar=('=COLUMN:VALUE'))

    args = parser.parse_args()

    columns_labels = CsvPedigreeReader.get_column_labels()
    if args.columns is not None:
        for option in args.columns:
            column, label = option.split(':')
            if label.isdigit():
                label = int(label)
            columns_labels[column] = label
    header = args.no_header
    if header:
        header = list(range(len(args.columns)))
    delimiter = args.delimiter

    pedigrees = CsvPedigreeReader().read_file(
        args.file, columns_labels, header, delimiter)

    pdf_drawer = PDFLayoutDrawer(args.output)
    layout_saver = None

    if args.save_layout:
        layout_saver = LayoutSaver(
            args.file, args.save_layout, args.layout_column)

    for family in sorted(pedigrees, key=lambda x: x.family_id):
        sandwich_instance = family.create_sandwich_instance()
        if sandwich_instance is None:
            print(family.family_id)
            print("Missing members")
            continue
        intervals = SandwichSolver.solve(sandwich_instance)

        if intervals is None:
            print(family.family_id)
            print("No intervals")
        if intervals:
            individuals_intervals = filter(
                lambda interval: interval.vertex.is_individual(),
                intervals
            )

            # print(family.family_id)
            layout = Layout(individuals_intervals)
            layout_drawer = OffsetLayoutDrawer(layout, 0, 0)
            pdf_drawer.add_page(layout_drawer.draw(), family.family_id)

            if layout_saver is not None:
                layout_saver.writerow(family, layout)

    pdf_drawer.save_file()
    if layout_saver:
        layout_saver.save()


if __name__ == "__main__":
    main()
