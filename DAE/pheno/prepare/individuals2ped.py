#!/usr/bin/env python2.7
import argparse
import csv
from collections import defaultdict
from pheno.common import Role
from pheno.common import RoleMapping


class Individual(object):

    def __init__(self, individual_id, family_id, sex, role):
        self.sex = sex
        self.individual_id = individual_id
        self.family_id = family_id
        self.role = RoleMapping.SPARK[role]

    def __repr__(self):
        return self.individual_id if self.individual_id is not None \
            else "UNKNOWN"


class IndividualUnit(object):

    def __init__(self, individual, mating_units=None,
                 parents=None):

        if mating_units is None:
            mating_units = []

        self.mating_units = mating_units
        self.parents = parents
        self.individual = individual

    def __repr__(self):
        return repr(self.individual)


NULL_INDIVIDUAL = IndividualUnit(individual=None)


class SibshipUnit(object):
    def __init__(self, individuals=None):
        if individuals is None:
            individuals = set()

        self.individuals = individuals


class MatingUnit(object):

    def __init__(self, mother, father, children=None):
        if children is None:
            children = SibshipUnit()

        self.mother = mother
        self.father = father
        self.children = children

        self.mother.mating_units.append(self)
        self.father.mating_units.append(self)


class SPARKCsvIndividualsReader(object):

    COLUMNS_TO_FIELDS = {
        'role': 'role',
        'family_id': 'family_id',
        'subject_sp_id': 'individual_id',
        'sex': 'sex'
    }

    def read_structure(self, individuals):
        families = defaultdict(list)
        for individual in individuals:
            families[individual.family_id].append(individual)

        return families

    def read_csv_file(self, csv_file):
        individuals = []
        reader = csv.DictReader(csv_file)
        for row in reader:
            kwargs = {
                field: row[column]
                for (column, field)
                in SPARKCsvIndividualsReader.COLUMNS_TO_FIELDS.items()
            }

            individuals.append(Individual(**kwargs))

        return self.read_structure(individuals)

    def read_filename(self, filename):
        with open(filename, 'r') as csv_file:
            families = self.read_csv_file(csv_file)

        return families


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', type=str)
    args = parser.parse_args()

    reader = SPARKCsvIndividualsReader()
    families = reader.read_filename(args.file)

    print(families)


if __name__ == '__main__':
    main()
