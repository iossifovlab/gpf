#!/usr/bin/env python2.7
import abc
import itertools
import argparse
import csv
from collections import defaultdict
from pheno.prepare.individuals2ped import \
    IndividualUnit, MatingUnit
from pheno.common import Status
from pheno.common import Gender
from pheno.common import Role


class PedigreeMember(object):

    def __init__(
            self, family_id, individual_id, mother_id, father_id, gender,
            status, role):
        self.family_id = family_id
        self.individual_id = individual_id
        self.mother_id = mother_id
        self.father_id = father_id
        self.gender = gender
        self.status = status
        self.role = role

    def __repr__(self):
        return self.individual_id

    def assign_role(self, role):
        assert self.role == Role.unknown or self.role == role, \
            "{},{},{}!={}".format(
                self.family_id, self.individual_id, self.role, role)
        self.role = role


class CsvPedigreeReader(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def convert_individual_id(self, family_id, individual_id):
        raise NotImplementedError()

    @abc.abstractmethod
    def convert_status(self, status):
        raise NotImplementedError()

    @abc.abstractmethod
    def convert_gender(self, gender):
        raise NotImplementedError()

    @abc.abstractproperty
    def COLUMNS_TO_FIELDS(self):
        raise NotImplementedError()

    def read_structure(self, individuals):
        families = defaultdict(list)
        for individual in individuals:
            families[individual.family_id].append(individual)

        return families

    def read_csv_file(self, csv_file):
        individuals = []
        reader = csv.DictReader(csv_file, delimiter='\t')
        for row in reader:
            kwargs = {
                field: row[column]
                for (column, field) in self.COLUMNS_TO_FIELDS.items()
            }

            kwargs['individual_id'] = self.convert_individual_id(
                kwargs['family_id'], kwargs['individual_id'])
            kwargs['mother_id'] = self.convert_individual_id(
                kwargs['family_id'], kwargs['mother_id'])
            kwargs['father_id'] = self.convert_individual_id(
                kwargs['family_id'], kwargs['father_id'])

            kwargs["status"] = Status(self.convert_status(kwargs["status"]))
            kwargs["gender"] = Gender(self.convert_gender(kwargs["gender"]))
            kwargs["role"] = Role.unknown

            individual = PedigreeMember(**kwargs)

            individuals.append(individual)

        return self.read_structure(individuals)

    def read_filename(self, filename):
        with open(filename, "r") as csv_file:
            families = self.read_csv_file(csv_file)

        return families


class SPARKCsvPedigreeReader(CsvPedigreeReader):

    @property
    def COLUMNS_TO_FIELDS(self):
        return {
            "familyId": "family_id",
            "personId": "individual_id",
            "momId": "mother_id",
            "dadId": "father_id",
            "gender": "gender",
            "status": "status"
        }

    def convert_status(self, val):
        return int(val)

    def convert_gender(self, val):
        return int(val)

    def convert_individual_id(self, _family_id, individual_id):
        return individual_id


class AGRERawCsvPedigreeReader(CsvPedigreeReader):

    @property
    def COLUMNS_TO_FIELDS(self):
        return {
            "family_id": "family_id",
            "Person": "individual_id",
            "Mother": "mother_id",
            "Father": "father_id",
            "Sex": "gender",
            "Scored Affected Status": "status"
        }

    def convert_status(self, val):
        if val:
            return Status.affected.value
        else:
            return Status.unaffected.value

    def convert_gender(self, val):
        if val == 'Female':
            return Gender.F.value
        elif val == 'Male':
            return Gender.M.value
        else:
            raise ValueError("unexpected sex: {}".format(val))

    def convert_individual_id(self, family_id, individual_id):
        assert isinstance(individual_id, str)

        if individual_id == '0' or individual_id == 0:
            return '0'
        res = "{}{:02d}".format(family_id, int(individual_id))
        return res


class PedigreeToFamily(object):

    def _link_pedigree_members(self, members):
        individuals = []
        individuals_by_id = {}
        mating_units_by_id = {}

        for member in members:
            if member.individual_id not in individuals_by_id:
                individuals_by_id[member.individual_id] = IndividualUnit()
            individual = individuals_by_id[member.individual_id]
            individual.individual = member

            individuals.append(individual)

        for individual in individuals:
            father_id = individual.individual.father_id
            mother_id = individual.individual.mother_id

            if mother_id != "0" or father_id != "0":

                mating_unit_id = "{},{}".format(mother_id, father_id)
                if mating_unit_id not in mating_units_by_id:
                    mother = None
                    if mother_id in individuals_by_id:
                        mother = individuals_by_id[mother_id]
                    father = None
                    if father_id in individuals_by_id:
                        father = individuals_by_id[father_id]

                    mating_units_by_id[mating_unit_id] = \
                        MatingUnit(mother=mother, father=father)

                parents = mating_units_by_id[mating_unit_id]
                individual.parents = parents
                parents.children.individuals.add(individual)

        return individuals

    def _assign_roles_paternal_other_families(self, father):
        for other_mating_unit in father.mating_units:
            if not other_mating_unit.mother.has_individual():
                continue

            if other_mating_unit.mother.individual.role != Role.mom:
                other_mating_unit.mother.individual.assign_role(Role.step_mom)
            for child in other_mating_unit.children.individuals:
                if not child.individual.role:
                    child.individual.assign_role(Role.paternal_half_sibling)

    def _assign_roles_paternal(self, father):
        if father.parents:
            grandparents = father.parents

            if grandparents.father.has_individual():
                grandparents.father.individual.assign_role(
                    Role.paternal_grandfather)

            if grandparents.mother.has_individual():
                grandparents.mother.individual.assign_role(
                    Role.paternal_grandmother)

            for individual in grandparents.children.individuals:
                if (not individual.has_individual()
                        or individual.individual.role):
                    continue

                if individual.individual.gender == Gender.M:
                    individual.individual.assign_role(Role.paternal_uncle)
                if individual.individual.gender == Gender.F:
                    individual.individual.assign_role(Role.paternal_aunt)

                self._assign_roles_paternal_cousin(individual)

        self._assign_roles_paternal_other_families(father)

    def _assign_roles_maternal_other_families(self, mother):
        for other_mating_unit in mother.mating_units:
            if not other_mating_unit.father.has_individual():
                continue

            if other_mating_unit.father.individual.role != Role.dad:
                other_mating_unit.father.individual.assign_role(Role.step_dad)
            for child in other_mating_unit.children.individuals:
                if not child.individual.role:
                    child.individual.assign_role(Role.maternal_half_sibling)

    def _assign_roles_maternal(self, mother):
        if mother.parents:
            grandparents = mother.parents

            if grandparents.father.has_individual():
                grandparents.father.individual.assign_role(
                    Role.maternal_grandfather)

            if grandparents.mother.has_individual():
                grandparents.mother.individual.assign_role(
                    Role.maternal_grandmother)

            for individual in grandparents.children.individuals:
                if (not individual.has_individual()
                        or individual.individual.role):
                    continue

                if individual.individual.gender == Gender.M:
                    individual.individual.assign_role(Role.maternal_uncle)
                if individual.individual.gender == Gender.F:
                    individual.individual.assign_role(Role.maternal_aunt)

                self._assign_roles_maternal_cousin(individual)

        self._assign_roles_maternal_other_families(mother)

    def _assign_roles_maternal_cousin(self, uncle_or_aunt):
        for mating_unit in uncle_or_aunt.mating_units:
            for child in mating_unit.children.individuals:
                child.individual.assign_role(Role.maternal_cousin)

    def _assign_roles_paternal_cousin(self, uncle_or_aunt):
        for mating_unit in uncle_or_aunt.mating_units:
            for child in mating_unit.children.individuals:
                child.individual.assign_role(Role.paternal_cousin)

    def _assign_roles_children(self, proband):
        for mating_unit in proband.mating_units:
            for child in mating_unit.children.individuals:
                child.individual.assign_role(Role.child)

    def _assign_roles_mates(self, proband):
        for mating_unit in proband.mating_units:
            if (mating_unit.father != proband
                    and mating_unit.father.has_individual()):
                mating_unit.father.individual.assign_role(Role.spouse)
            elif (mating_unit.mother != proband
                    and mating_unit.mother.has_individual()):
                mating_unit.mother.individual.assign_role(Role.spouse)

    def _assign_roles(self, proband):
        proband.individual.assign_role(Role.prb)

        self._assign_roles_children(proband)
        self._assign_roles_mates(proband)

        if not proband.parents:
            return

        parents = proband.parents

        for individual in parents.children.individuals:
            if individual != proband:
                individual.individual.assign_role(Role.sib)

        if parents.father.has_individual():
            father = proband.get_father_individual()
            father.individual.assign_role(Role.dad)

        if parents.mother.has_individual():
            mother = proband.get_mother_individual()
            mother.individual.assign_role(Role.mom)

        if parents.father.has_individual():
            father = proband.get_father_individual()
            self._assign_roles_paternal(father)

        if parents.mother.has_individual():
            mother = proband.get_mother_individual()
            self._assign_roles_maternal(mother)

    def to_family(self, members):
        individuals = self._link_pedigree_members(members)
        affected = filter(
            lambda x: x.individual.status == Status.affected, individuals)
        proband = sorted(
            affected, key=lambda x: x.individual.individual_id)[0]

        self._assign_roles(proband)

        return individuals

    def build_families(self, families):
        pedigrees = {}

        for family_name, members in families.items():
            pedigree = self.to_family(members)
            pedigrees[family_name] = pedigree

        return pedigrees


class FamilyToCsv(object):

    def __init__(self, filename):
        self.filename = filename

    def write_pedigrees(self, pedigrees):
        with open(self.filename, "w") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow([
                "familyId", "individualId", "gender",
                "status", "role"])
            writer.writerows(map(self.get_row, pedigrees))

    @staticmethod
    def get_row(individual):
        return [
            individual.individual.family_id,
            individual.get_individual_id(),
            individual.get_gender(),
            individual.get_status(),
            individual.get_role()
        ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str)
    parser.add_argument("--output", dest="output", default="output.ped",
                        type=str)
    args = parser.parse_args()

    reader = AGRERawCsvPedigreeReader()
    families = reader.read_filename(args.file)

    pedigrees = {}

    for family_name, members in families.items():
        pedigree = PedigreeToFamily().to_family(members)
        pedigrees[family_name] = pedigree

    pedigrees_list = list(itertools.chain(*pedigrees.values()))

    FamilyToCsv(args.output).write_pedigrees(pedigrees_list)


if __name__ == "__main__":
    main()
