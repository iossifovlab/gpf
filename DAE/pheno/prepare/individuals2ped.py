#!/usr/bin/env python2.7
import itertools
import argparse
import csv
from collections import defaultdict
from pheno.common import Role
from pheno.common import RoleMapping
from pheno.common import Status
from pheno.common import Gender


class Individual(object):

    def __init__(self, individual_id, family_id, gender, role, status):
        self.gender = gender
        self.individual_id = individual_id
        self.family_id = family_id
        self.role = role
        self.status = status

    def __repr__(self):
        return "Individual({})".format(
            str(self.individual_id) if self.individual_id is not None
            else "UNKNOWN")


class IndividualUnit(object):
    NO_RANK = -3673473456

    def __init__(self, individual=None, mating_units=None,
                 parents=None, rank=NO_RANK):

        if mating_units is None:
            mating_units = []

        self.mating_units = mating_units
        self.parents = parents
        self.individual = individual
        self.rank = rank

        if parents:
            parents.children.individuals.add(self)

    def __repr__(self):
        return repr(self.individual) + " (" + str(self.rank) + ")"

    def add_ranks(self):
        self._add_rank(0)

    def _add_rank(self, rank):
        if self.rank != IndividualUnit.NO_RANK:
            return

        self.rank = rank

        for mu in self.mating_units:
            for child in mu.children.individuals:
                child._add_rank(rank - 1)

            mu.father._add_rank(rank)
            mu.mother._add_rank(rank)

        if self.parents:
            if self.parents.father:
                self.parents.father._add_rank(rank + 1)
            if self.parents.mother:
                self.parents.mother._add_rank(rank + 1)

    def has_individual(self):
        return bool(self.individual)

    # methods for traversal
    def get_or_create_parents(self):
        if not self.parents:
            self.parents = MatingUnit()

        return self.parents

    def get_or_create_sibship(self):
        parents = self.get_or_create_parents()
        return parents.children

    def get_father_individual(self):
        return self.get_or_create_parents().father

    def get_mother_individual(self):
        return self.get_or_create_parents().mother

    def get_sibling_individual(self):
        parents = self.get_or_create_parents()
        return IndividualUnit(None, parents=parents)

    def get_maternal_aunt(self):
        return self.get_mother_individual().get_sibling_individual()

    def get_maternal_uncle(self):
        return self.get_mother_individual().get_sibling_individual()

    def get_paternal_aunt(self):
        return self.get_father_individual().get_sibling_individual()

    def get_paternal_uncle(self):
        return self.get_father_individual().get_sibling_individual()

    def get_paternal_grandfather(self):
        return self.get_father_individual().get_father_individual()

    def get_paternal_grandmother(self):
        return self.get_father_individual().get_mother_individual()

    def get_maternal_grandfather(self):
        return self.get_mother_individual().get_father_individual()

    def get_maternal_grandmother(self):
        return self.get_mother_individual().get_mother_individual()

    def get_paternal_half_sibling(self):
        father = self.get_father_individual()

        new_mating_unit = MatingUnit(mother=None, father=father)

        return IndividualUnit(None, parents=new_mating_unit)

    def get_maternal_half_sibling(self):
        mother = self.get_mother_individual()

        new_mating_unit = MatingUnit(mother=mother, father=None)

        return IndividualUnit(None, parents=new_mating_unit)

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
            return 'UNKNOWN'
        return self.individual.gender.value

    def get_status(self):
        if not self.individual:
            return 'UNKNOWN'
        return self.individual.status.value

    def get_role(self):
        if not self.individual or not self.individual.role:
            return 'UNKNOWN'
        return self.individual.role.name


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
        "sex": "gender",
        "asd": "status"
    }

    STATUS_TO_ENUM = {
        "True": Status.affected,
        "False": Status.unaffected
    }

    GENDER_TO_ENUM = {
        "Male": Gender.M,
        "Female": Gender.F
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
            kwargs["role"] = RoleMapping.SPARK[kwargs["role"]]
            kwargs["status"] = SPARKCsvIndividualsReader \
                .STATUS_TO_ENUM[kwargs["status"]]
            kwargs["gender"] = SPARKCsvIndividualsReader \
                .GENDER_TO_ENUM[kwargs["gender"]]

            individuals.append(Individual(**kwargs))

        return self.read_structure(individuals)

    def read_filename(self, filename):
        with open(filename, "r") as csv_file:
            families = self.read_csv_file(csv_file)

        return families


class FamilyToPedigree(object):

    def get_individual(self, proband, role):
        if role == Role.dad:
            return proband.get_father_individual()

        if role == Role.mom:
            return proband.get_mother_individual()

        if role == Role.sib:
            return proband.get_sibling_individual()

        if role == Role.maternal_aunt:
            return proband.get_maternal_aunt()

        if role == Role.maternal_uncle:
            return proband.get_maternal_uncle()

        if role == Role.paternal_aunt:
            return proband.get_paternal_aunt()

        if role == Role.paternal_uncle:
            return proband.get_paternal_uncle()

        if role == Role.paternal_grandfather:
            return proband.get_paternal_grandfather()

        if role == Role.paternal_grandmother:
            return proband.get_paternal_grandmother()

        if role == Role.maternal_grandfather:
            return proband.get_maternal_grandfather()

        if role == Role.maternal_grandmother:
            return proband.get_maternal_grandmother()

        if role == Role.paternal_half_sibling:
            return proband.get_paternal_half_sibling()

        if role == Role.maternal_half_sibling:
            return proband.get_maternal_half_sibling()

        raise NotImplementedError("Unknown individual role: {}".format(role))

    def to_pedigree(self, family_members):
        individual_id_to_individual_unit = {}
        proband = [individual for individual in family_members
                   if individual.role == Role.prb]
        assert len(proband) == 1
        proband = proband[0]

        other = [individual for individual in family_members
                 if individual.role != Role.prb]

        proband_unit = IndividualUnit(proband)
        individual_id_to_individual_unit[proband.individual_id] = proband_unit

        for individual in other:
            individual_unit = self.get_individual(
                proband_unit, individual.role)
            individual_unit.individual = individual
            individual_id_to_individual_unit[individual.individual_id] = \
                individual_unit

        return individual_id_to_individual_unit


class PedigreeToCsv(object):

    def __init__(self, filename):
        self.filename = filename

    def write_pedigrees(self, pedigrees):
        with open(self.filename, "w") as csv_file:
            writer = csv.writer(csv_file, delimiter='\t')
            writer.writerow([
                "familyId", "personId", "dadId", "momId", "gender",
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
            individual.get_status(),
            individual.get_role()
        ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str)
    parser.add_argument(
        "--output", dest="output", default="output.ped", type=str)
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
