from __future__ import print_function
from __future__ import absolute_import
from builtins import open
from builtins import str
import collections
import csv


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
                self.generated_column: '1' if member.generated else ''
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
                self.generated_column: '1'
                if position.individual.member.generated else ''
            }

            key = self._member_key(family.family_id, individual_id)

            self._people_with_layout[key] = row
            self._people[key] = position.individual.member

    def write(self, family, layout):
        if isinstance(layout, Layout):
            self.writerow(family, layout)
        else:
            self.writerow_error(family, layout)

    def save(self, columns_labels, header=None, delimiter="\t"):
        with open(self.input_filename, "r") as input_file, \
                open(self.output_filename, "w") as output_file:

            reader = csv.DictReader(
                input_file, fieldnames=header, delimiter=delimiter,
                lineterminator='\n')
            fieldnames = list(str(field) for field in reader.fieldnames)
            # print(fieldnames, type(fieldnames[0]))

            # assert self.fieldname not in fieldnames, \
            #     "{} already in file {}".format(
            #         self.fieldname, self.input_filename)

            if self.fieldname not in fieldnames:
                fieldnames.append(self.fieldname)
            if self.generated_column not in fieldnames:
                fieldnames.append(self.generated_column)

            writer = csv.DictWriter(output_file, fieldnames, delimiter="\t")

            writer.writeheader()

            for row in reader:
                row_copy = row.copy()

                key = self._member_key(row[columns_labels["family_id"]],
                                       row[columns_labels["id"]])

                if key in self._people_with_layout:
                    member = self._people[key]

                    row_copy[columns_labels["mother"]] = member.mother
                    row_copy[columns_labels["father"]] = member.father

                    row_copy.update(self._people_with_layout.pop(key))
                else:
                    row_copy[self.fieldname] = ""
                    row_copy[self.generated_column] = ""

                writer.writerow(row_copy)

            for generated_id, generated_layout in\
                    self._people_with_layout.items():
                row = {fieldname: '' for fieldname in fieldnames}

                family_id, person_id = generated_id.split(";")
                key = self._member_key(family_id, person_id)
                member = self._people[key]

                row[columns_labels["family_id"]] = family_id
                row[columns_labels["id"]] = person_id
                row[columns_labels["mother"]] = member.mother
                row[columns_labels["father"]] = member.father
                row[columns_labels["sex"]] = member.sex
                row[columns_labels["status"]] = member.status
                row[columns_labels["role"]] = member.role
                row.update(generated_layout)

                writer.writerow(row)
