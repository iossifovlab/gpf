#!/usr/bin/env python
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals
import collections
import csv

from pedigrees.pedigree_reader import PedigreeReader
from pedigrees.pedigrees import get_argument_parser, FamilyConnections
from pedigrees.interval_sandwich import SandwichSolver
from pedigrees.layout import Layout


class LayoutSaver(object):

    def __init__(self, input_filename, output_filename, generated_column,
                 fieldname):
        self.input_filename = input_filename
        self.output_filename = output_filename
        self.generated_column = generated_column
        self.fieldname = fieldname
        self._people_with_layout = collections.OrderedDict()
        self._people = collections.OrderedDict()

    @staticmethod
    def _member_key(family_id, individual_id):
        return "{};{}".format(family_id, individual_id)

    def writerow_error(self, family, error):
        for member in family.members:
            row = {
                self.fieldname: error,
                self.generated_column: '' if member.effect != '-' else '1'
            }

            key = self._member_key(family.family_id, member.id)

            self._people_with_layout[key] = row
            self._people[key] = member

    def writerow(self, family, layout):
        individuals_by_rank = layout.individuals_by_rank
        for individual_id, position in list(layout.id_to_position.items()):
            row = {
                self.fieldname: "{}:{},{}".format(
                    individuals_by_rank[individual_id], position.x,
                    position.y),
                self.generated_column:
                    '' if position.individual.member.effect != '-' else '1'
            }

            key = self._member_key(family.family_id, individual_id)

            self._people_with_layout[key] = row
            self._people[key] = position.individual.member

    def save(self, columns_labels, header=None, delimiter="\t"):
        with open(self.input_filename, "r") as input_file, \
                open(self.output_filename, "w") as output_file:

            reader = csv.DictReader(input_file, fieldnames=header,
                                    delimiter=delimiter)
            fieldnames = list(reader.fieldnames)

            assert self.fieldname not in fieldnames, \
                "{} already in file {}".format(
                    self.fieldname, self.input_filename)

            writer = csv.DictWriter(
                output_file,
                reader.fieldnames + [self.fieldname, self.generated_column],
                delimiter='\t')

            writer.writeheader()

            for row in reader:
                row_copy = row.copy()

                key = self._member_key(row[columns_labels["family_id"]],
                                       row[columns_labels["id"]])

                member = self._people[key]

                row_copy[columns_labels["mother"]] = member.mother
                row_copy[columns_labels["father"]] = member.father

                if key in self._people_with_layout:
                    row_copy.update(self._people_with_layout.pop(key))
                else:
                    row_copy[self.fieldname] = ""
                    row_copy[self.generated_column] = ""

                writer.writerow(row_copy)

            for generated_id, generated_layout in\
                    self._people_with_layout.items():
                row = {fieldname: ''
                       for fieldname in
                       fieldnames + [self.fieldname, self.generated_column]}

                family_id, person_id = generated_id.split(";")
                key = self._member_key(family_id, person_id)
                member = self._people[key]

                row[columns_labels["family_id"]] = family_id
                row[columns_labels["id"]] = person_id
                row[columns_labels["mother"]] = member.mother
                row[columns_labels["father"]] = member.father
                row[columns_labels["sex"]] = member.sex
                row[columns_labels["effect"]] = member.effect
                row.update(generated_layout)

                writer.writerow(row)


def main():
    parser = get_argument_parser("Save PDP.")
    args = parser.parse_args()

    columns_labels = {
        "family_id": args.family_id,
        "id": args.id,
        "father": args.father,
        "mother": args.mother,
        "sex": args.sex,
        "effect": args.effect,
        "layout": ""
    }
    header = args.no_header_order
    if header:
        header = header.split(',')
    delimiter = args.delimiter

    pedigrees = PedigreeReader().read_file(
        args.file, columns_labels, header, delimiter)

    layout_saver = LayoutSaver(
        args.file, args.output, args.generated_column, args.layout_column)

    for family in sorted(pedigrees, key=lambda x: x.family_id):
        family_connections = FamilyConnections.from_pedigree(family)
        if family_connections is None:
            layout_saver.writerow_error(family, "Missing members")
            print(family.family_id)
            print("Missing members")
            continue
        sandwich_instance = family_connections.create_sandwich_instance()
        intervals = SandwichSolver.solve(sandwich_instance)

        if intervals is None:
            layout_saver.writerow_error(family, "No intervals")
            print(family.family_id)
            print("No intervals")
        if intervals:
            individuals_intervals = filter(
                lambda interval: interval.vertex.is_individual(),
                intervals
            )

            # print(family.family_id)
            layout = Layout(individuals_intervals)
            layout_saver.writerow(family, layout)

    layout_saver.save(columns_labels, header, delimiter)


if __name__ == '__main__':
    main()
