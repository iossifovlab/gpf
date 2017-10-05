#!/usr/bin/env python2.7
import itertools
import argparse
import csv
from collections import defaultdict
from pheno.common import Role
from pheno.common import RoleMapping


class Individual(object):

    def __init__(self, individual_id, family_id, sex, role, affected):
        self.sex = sex
        self.individual_id = individual_id
        self.family_id = family_id
        self.role = RoleMapping.SPARK[role]
        self.affected = affected

    def __repr__(self):
        return self.individual_id if self.individual_id is not None \
            else "UNKNOWN"


class IndividualUnit(object):

    def __init__(self, individual=None, mating_units=None,
                 parents=None):

        if mating_units is None:
            mating_units = []

        self.mating_units = mating_units
        self.parents = parents
        self.individual = individual

        if parents:
            parents.children.individuals.add(self)

    def __repr__(self):
        return repr(self.individual)

    def get_or_create_parents(self):
        if not self.parents:
            self.parents = MatingUnit()

        return self.parents

    def get_or_create_sibship(self):
        parents = self.get_or_create_parents()
        return parents.children

    # methods for visualisation
    def get_individual_id(self):
        if self.individual:
            return self.individual.individual_id
        return 0

    def get_father_id(self):
        if not self.parents:
            return 0
        return self.parents.father.get_individual_id()

    def get_mother_id(self):
        if not self.parents:
            return 0
        return self.parents.mother.get_individual_id()

    def get_gender(self):
        if not self.individual:
            return 'unknown'
        return 1 if self.individual.sex == 'Male' else 2

    def get_affected(self):
        if not self.individual:
            return 'unknown'
        return 1 if self.individual.affected == 'False' else 2


class SibshipUnit(object):
    def __init__(self, individuals=None):
        if individuals is None:
            individuals = set()

        self.individuals = individuals


class MatingUnit(object):

    def __init__(self, mother=None, father=None, children=None):
        if children is None:
            children = SibshipUnit()

        if mother is None:
            mother = IndividualUnit()

        if father is None:
            father = IndividualUnit()

        self.mother = mother
        self.father = father
        self.children = children

        self.mother.mating_units.append(self)
        self.father.mating_units.append(self)


class SPARKCsvIndividualsReader(object):

    COLUMNS_TO_FIELDS = {
        "role": "role",
        "family_id": "family_id",
        "subject_sp_id": "individual_id",
        "sex": "sex",
        "asd": "affected"
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
        with open(filename, "r") as csv_file:
            families = self.read_csv_file(csv_file)

        return families


class FamilyToPedigree(object):
    def get_father_individual(self, individual):
        return individual.get_or_create_parents().father

    def get_mother_individual(self, individual):
        return individual.get_or_create_parents().mother

    def get_sibling_individual(self, individual):
        parents = individual.get_or_create_parents()
        return IndividualUnit(None, parents=parents)

    def get_maternal_aunt(self, individual):
        return self.get_sibling_individual(
            self.get_mother_individual(individual))

    def get_maternal_uncle(self, individual):
        return self.get_sibling_individual(
            self.get_mother_individual(individual))

    def get_paternal_aunt(self, individual):
        return self.get_sibling_individual(
            self.get_father_individual(individual))

    def get_paternal_uncle(self, individual):
        return self.get_sibling_individual(
            self.get_father_individual(individual))

    def get_paternal_grandfather(self, individual):
        return self.get_father_individual(
            self.get_father_individual(individual))

    def get_paternal_grandmother(self, individual):
        return self.get_mother_individual(
            self.get_father_individual(individual))

    def get_maternal_grandfather(self, individual):
        return self.get_father_individual(
            self.get_mother_individual(individual))

    def get_maternal_grandmother(self, individual):
        return self.get_mother_individual(
            self.get_mother_individual(individual))

    def get_paternal_half_sibling(self, individual):
        father = self.get_mother_individual(individual)

        new_mating_unit = MatingUnit()
        new_mating_unit.father = father

        father.mating_units.append(new_mating_unit)

        return IndividualUnit(None, parents=new_mating_unit)

    def get_maternal_half_sibling(self, individual):
        mother = self.get_mother_individual(individual)

        new_mating_unit = MatingUnit()
        new_mating_unit.mother = mother

        mother.mating_units.append(new_mating_unit)

        return IndividualUnit(None, parents=new_mating_unit)

    def get_individual(self, probant, role):
        if role == Role.dad:
            return self.get_father_individual(probant)

        if role == Role.mom:
            return self.get_mother_individual(probant)

        if role == Role.sib:
            return self.get_sibling_individual(probant)

        if role == Role.maternal_aunt:
            return self.get_maternal_aunt(probant)

        if role == Role.maternal_uncle:
            return self.get_maternal_uncle(probant)

        if role == Role.paternal_aunt:
            return self.get_paternal_aunt(probant)

        if role == Role.paternal_uncle:
            return self.get_paternal_uncle(probant)

        if role == Role.paternal_grandfather:
            return self.get_paternal_grandfather(probant)

        if role == Role.paternal_grandmother:
            return self.get_paternal_grandmother(probant)

        if role == Role.maternal_grandfather:
            return self.get_maternal_grandfather(probant)

        if role == Role.maternal_grandmother:
            return self.get_maternal_grandmother(probant)

        if role == Role.paternal_half_sibling:
            return self.get_paternal_half_sibling(probant)

        if role == Role.maternal_half_sibling:
            return self.get_maternal_half_sibling(probant)

        raise NotImplementedError("Unknown individual role: {}".format(role))

    def to_pedigree(self, family_members):
        individual_id_to_individual_unit = {}
        probant = [individual for individual in family_members
                   if individual.role == Role.prb]
        assert len(probant) == 1
        probant = probant[0]

        other = [individual for individual in family_members
                 if individual.role != Role.prb]

        probant_unit = IndividualUnit(probant)
        individual_id_to_individual_unit[probant.individual_id] = probant_unit

        for individual in other:
            individual_unit = self.get_individual(probant_unit, individual.role)
            individual_unit.individual = individual
            individual_id_to_individual_unit[individual.individual_id] = \
                individual_unit

        return individual_id_to_individual_unit


class PedigreeToCsv(object):

    def __init__(self, filename):
        self.filename = filename

    def write_pedigrees(self, pedigrees):
        with open(self.filename, "w") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow([
                "familyId", "individualId", "dadId", "momId", "gender",
                "status", "role"])
            writer.writerows(map(self.get_row, pedigrees))

    @staticmethod
    def get_row(individual):
        return [
            individual.individual.family_id,
            individual.get_individual_id(),
            individual.get_father_id(),
            individual.get_mother_id(),
            individual.get_gender(),
            individual.get_affected(),
            individual.individual.role.name
        ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str)
    parser.add_argument("--output", dest="output", default="output.ped", type=str)
    args = parser.parse_args()

    reader = SPARKCsvIndividualsReader()
    families = reader.read_filename(args.file)

    pedigrees = {}

    for family_name, members in families.items():
        pedigree = FamilyToPedigree().to_pedigree(members)
        pedigrees[family_name] = pedigree.values()

    pedigrees_list = list(itertools.chain(*pedigrees.values()))

    PedigreeToCsv(args.output).write_pedigrees(pedigrees_list)


if __name__ == "__main__":
    main()
