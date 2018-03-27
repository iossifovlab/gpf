#!/usr/bin/env python2.7
import argparse
import csv
import collections

from interval_sandwich import SandwichInstance, SandwichSolver
from layout import Layout
from drawing import PDFLayoutDrawer, OffsetLayoutDrawer
from pedigree_reader import PedigreeReader
from pedigrees import FamilyConnections


def create_sandwich_instance(family):
    family_connections = FamilyConnections.from_pedigree(family)
    id_to_individual = family_connections.id_to_individual
    id_to_mating_unit = family_connections.id_to_mating_unit

    individuals = set(id_to_individual.values())
    mating_units = set(id_to_mating_unit.values())
    sibship_units = set([mu.children for mu in id_to_mating_unit.values()])

    all_vertices = individuals | mating_units | sibship_units

    family_connections.add_ranks()

    # if len(individuals) != 0:
    #     individuals.__iter__().next().add_rank(0)
    #     _fix_rank(individuals)

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
        for individual_id, position in layout.id_to_position.items():
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

    args = parser.parse_args()
    pedigrees = PedigreeReader().read_file(args.file)

    pdf_drawer = PDFLayoutDrawer(args.output)
    layout_saver = None

    if args.save_layout:
        layout_saver = LayoutSaver(
            args.file, args.save_layout, args.layout_column)

    for family in sorted(pedigrees, key=lambda x: x.family_id):
        sandwich_instance = create_sandwich_instance(family)
        intervals = SandwichSolver.solve(sandwich_instance)

        if intervals is None:
            print(family.family_id)
            print("No intervals")
        if intervals:
            individuals_intervals = filter(
                lambda interval: interval.vertex.is_individual(),
                intervals
            )
            mating_units = {mu for i in individuals_intervals
                            for mu in i.vertex.mating_units}
            if len(mating_units) > 1:
                print(family.family_id)
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
