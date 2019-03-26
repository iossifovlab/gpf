#!/usr/bin/env python

from builtins import map
from builtins import object
import abc
import itertools
import argparse
import csv
from collections import defaultdict
from pheno.prepare.individuals2ped import \
    IndividualUnit, MatingUnit
from future.utils import with_metaclass
from variants.attributes import Role, Sex, Status


class PedigreeError(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class NoProband(PedigreeError):
    pass


class PedigreeMember(object):

    def __init__(
            self, family_id, individual_id, mother_id, father_id, sex,
            status, role):
        self.family_id = family_id
        self.individual_id = individual_id
        self.mother_id = mother_id
        self.father_id = father_id
        self.sex = sex
        self.status = status
        self.role = role

    def __repr__(self):
        return self.individual_id

    def assign_role(self, role):
        assert not self.has_role() or self.role == role, \
            "{},{},{}!={}".format(
                self.family_id, self.individual_id, self.role, role)
        self.role = role

    def has_role(self):
        return self.role != Role.unknown


class CsvPedigreeReader(with_metaclass(abc.ABCMeta, object)):
    @abc.abstractmethod
    def convert_individual_id(self, family_id, individual_id):
        raise NotImplementedError()

    @abc.abstractmethod
    def convert_status(self, status):
        raise NotImplementedError()

    @abc.abstractmethod
    def convert_sex(self, sex):
        raise NotImplementedError()

    @abc.abstractproperty
    def COLUMNS_TO_FIELDS(self):
        raise NotImplementedError()

    @staticmethod
    def read_structure(individuals):
        families = defaultdict(list)
        for individual in individuals:
            families[individual.family_id].append(individual)

        return families

    def read_csv_file(self, csv_file, delimiter="\t"):
        individuals = []
        reader = csv.DictReader(csv_file, delimiter=delimiter)
        for row in reader:
            kwargs = {
                field: row[column]
                for (column, field) in list(self.COLUMNS_TO_FIELDS.items())
            }

            kwargs["individual_id"] = self.convert_individual_id(
                kwargs["family_id"], kwargs["individual_id"])
            kwargs["mother_id"] = self.convert_individual_id(
                kwargs["family_id"], kwargs["mother_id"])
            kwargs["father_id"] = self.convert_individual_id(
                kwargs["family_id"], kwargs["father_id"])

            kwargs["status"] = self.convert_status(kwargs["status"])
            kwargs["sex"] = self.convert_sex(kwargs["sex"])
            kwargs["role"] = Role.unknown

            individual = PedigreeMember(**kwargs)

            individuals.append(individual)

        return CsvPedigreeReader.read_structure(individuals)

    def read_filename(self, filename, delimiter="\t"):
        with open(filename, "r") as csv_file:
            families = self.read_csv_file(csv_file, delimiter=delimiter)

        return families


class SPARKCsvPedigreeReader(CsvPedigreeReader):

    @property
    def COLUMNS_TO_FIELDS(self):
        return {
            "familyId": "family_id",
            "personId": "individual_id",
            "momId": "mother_id",
            "dadId": "father_id",
            "sex": "sex",
            "status": "status"
        }

    def convert_status(self, val):
        return Status.affected if int(val) == 2 else Status.unaffected

    def convert_sex(self, val):
        return Sex.male if int(val) == 1 else Sex.female

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
            "Sex": "sex",
            "Scored Affected Status": "status"
        }

    def convert_status(self, val):
        if val:
            return Status.affected
        else:
            return Status.unaffected

    def convert_sex(self, val):
        if val == "Female":
            return Sex.female
        elif val == "Male":
            return Sex.male
        else:
            raise ValueError("unexpected sex: {}".format(val))

    def convert_individual_id(self, family_id, individual_id):
        assert isinstance(individual_id, str)

        if individual_id == "0" or individual_id == 0:
            return "0"
        res = "{}{:02d}".format(family_id, int(individual_id))
        return res


class VIPCsvPedigreeReader(CsvPedigreeReader):

    @property
    def COLUMNS_TO_FIELDS(self):
        return {
            "family": "family_id",
            "sfari_id": "individual_id",
            "mother": "mother_id",
            "father": "father_id",
            "sex": "sex",
            "genetic_status_16p": "status"
        }

    SEX_TO_ENUM = {
        "male": Sex.male,
        "female": Sex.female
    }

    def convert_status(self, status):
        return Status.unaffected if status == 'negative' \
            else Status.affected

    def convert_sex(self, sex):
        return self.SEX_TO_ENUM[sex]

    def convert_individual_id(self, _family_id, individual_id):
        return individual_id


class PedigreeToFamily(object):

    def _get_or_create_new_individual(self, individuals_by_id, individual_id):
        if individual_id == "0":
            result = IndividualUnit()
        else:
            result = individuals_by_id[individual_id]

        return result

    def _link_pedigree_members(self, members):
        individuals = []
        individuals_by_id = defaultdict(IndividualUnit)
        mating_units_by_id = defaultdict(list)

        for member in members:
            individual = individuals_by_id[member.individual_id]
            individual.individual = member

            individuals.append(individual)

        for individual in individuals:
            father_id = individual.individual.father_id
            mother_id = individual.individual.mother_id
            mother = self._get_or_create_new_individual(
                individuals_by_id, mother_id)
            father = self._get_or_create_new_individual(
                individuals_by_id, father_id)

            mating_unit_id = "{},{}".format(mother_id, father_id)

            if (mother.has_individual() and father.has_individual()
                    and mating_unit_id in mating_units_by_id):
                assert len(mating_units_by_id[mating_unit_id]) == 1
                parents = mating_units_by_id[mating_unit_id][0]
            else:
                parents = MatingUnit(mother=mother, father=father)
                mating_units_by_id[mating_unit_id].append(parents)

            individual.parents = parents
            parents.children.individuals.add(individual)

        return individuals

    def _assign_roles_paternal_other_families(self, father, mother):
        for other_mating_unit in father.mating_units:
            if other_mating_unit.mother == mother:
                continue

            for child in other_mating_unit.children.individuals:
                child.individual.assign_role(Role.paternal_half_sibling)

            if other_mating_unit.mother.has_individual():
                other_mating_unit.mother.individual.assign_role(Role.step_mom)

    def _assign_roles_paternal(self, father, mother):
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
                        or individual.individual.has_role()):
                    continue

                if individual.individual.sex == Sex.male:
                    individual.individual.assign_role(Role.paternal_uncle)
                if individual.individual.sex == Sex.female:
                    individual.individual.assign_role(Role.paternal_aunt)

                self._assign_roles_paternal_cousin(individual)

        self._assign_roles_paternal_other_families(father, mother)

    def _assign_roles_maternal_other_families(self, father, mother):
        for other_mating_unit in mother.mating_units:
            if other_mating_unit.father == father:
                continue

            for child in other_mating_unit.children.individuals:
                child.individual.assign_role(Role.maternal_half_sibling)

            if other_mating_unit.father.has_individual():
                other_mating_unit.father.individual.assign_role(Role.step_dad)

    def _assign_roles_maternal(self, father, mother):
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
                        or individual.individual.has_role()):
                    continue

                if individual.individual.sex == Sex.male:
                    individual.individual.assign_role(Role.maternal_uncle)
                if individual.individual.sex == Sex.female:
                    individual.individual.assign_role(Role.maternal_aunt)

                self._assign_roles_maternal_cousin(individual)

        self._assign_roles_maternal_other_families(father, mother)

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

        father = proband.get_father_individual()
        if parents.father.has_individual():
            father.individual.assign_role(Role.dad)

        mother = proband.get_mother_individual()
        if parents.mother.has_individual():
            mother.individual.assign_role(Role.mom)

        if parents.father.has_individual():
            father = proband.get_father_individual()
            self._assign_roles_paternal(father, mother)

        if parents.mother.has_individual():
            mother = proband.get_mother_individual()
            self._assign_roles_maternal(father, mother)

    def to_family(self, members, family_id='unknown'):
        individuals = self._link_pedigree_members(members)

        proband = self.get_proband(individuals)
        if proband is None:
            raise NoProband("No proband in family '{}'".format(family_id))

        self._assign_roles(proband)

        return individuals

    def get_proband(self, individuals):
        affected = self.get_affected(individuals)
        if len(affected) == 0:
            return None
        return sorted(affected, key=lambda x: x.individual.individual_id)[0]

    def get_affected(self, individuals):
        return [
            x for x in individuals
            if x.individual.status == Status.affected
        ]

    def build_families(self, families):
        pedigrees = {}

        for family_name, members in list(families.items()):
            try:
                pedigree = self.to_family(members, family_name)
                pedigrees[family_name] = pedigree
            except NoProband:
                continue

        return pedigrees


class AGREPedigreeToFamily(PedigreeToFamily):

    def get_proband(self, individuals):
        individuals[0].add_ranks()
        affected = self.get_affected(individuals)
        if len(affected) == 0:
            return None
        return sorted(affected, key=lambda x: x.rank)[0]


class FamilyToCsv(object):

    def __init__(self, filename):
        self.filename = filename

    def write_pedigrees(self, pedigrees):
        with open(self.filename, "w") as csv_file:
            writer = csv.writer(csv_file, delimiter="\t")
            writer.writerow([
                "familyId", "personId", "dadId", "momId",
                "sex", "status", "role"])
            writer.writerows(list(map(self.get_row, pedigrees)))

    @staticmethod
    def get_row(individual):
        return [
            individual.individual.family_id,
            individual.get_individual_id(),
            individual.get_father_id(),
            individual.get_mother_id(),
            individual.get_sex(),
            individual.get_status(),
            individual.get_role()
        ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str)
    parser.add_argument("--output", dest="output", default="output.ped",
                        type=str)
    parser.add_argument("--pheno", dest="pheno", type=str)
    parser.add_argument("--delimiter", dest="delimiter", default="\t",
                        type=str)
    args = parser.parse_args()

    reader = None
    if args.pheno == 'spark':
        reader = SPARKCsvPedigreeReader()
    elif args.pheno == 'svip':
        reader = VIPCsvPedigreeReader()
    elif args.pheno == 'agre':
        reader = AGRERawCsvPedigreeReader()
    assert reader is not None

    delimiter = args.delimiter
    families = reader.read_filename(args.file, delimiter=delimiter)

    pedigrees = {}

    for family_name, members in list(families.items()):
        pedigree = AGREPedigreeToFamily().to_family(members)
        pedigrees[family_name] = pedigree

    pedigrees_list = list(itertools.chain(*list(pedigrees.values())))

    FamilyToCsv(args.output).write_pedigrees(pedigrees_list)


if __name__ == "__main__":
    main()
