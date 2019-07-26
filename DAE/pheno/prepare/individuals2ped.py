#!/usr/bin/env python

import sys
import abc
import itertools
import argparse
import csv
from collections import defaultdict, OrderedDict
from variants.attributes import Role, Status, Sex
from pheno.common import RoleMapping


class Individual(object):

    def __init__(self, individual_id, family_id, sex, role, status):
        self.sex = sex
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
        return '0'

    def get_father_id(self):
        if not self.parents:
            return '0'
        return self.parents.father.get_individual_id()

    def get_mother_id(self):
        if not self.parents:
            return '0'
        return self.parents.mother.get_individual_id()

    def get_sex(self):
        if not self.individual:
            return 'UNKNOWN'

        return self.individual.sex.value

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


class CsvIndividualsReader(abc.ABCMeta, object):
    @abc.abstractmethod
    def convert_individual_id(self, family_id, individual_id):
        raise NotImplementedError()

    @abc.abstractmethod
    def convert_status(self, status):
        raise NotImplementedError()

    @abc.abstractmethod
    def convert_role(self, role):
        raise NotImplementedError()

    @abc.abstractmethod
    def convert_sex(self, sex):
        raise NotImplementedError()

    def convert_family_id(self, family_id):
        return family_id

    @abc.abstractproperty
    def FIELDS_TO_COLUMNS(self):
        raise NotImplementedError()

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
                for (field, column)
                in list(self.FIELDS_TO_COLUMNS.items())
            }
            kwargs["family_id"] = self.convert_family_id(kwargs["family_id"])
            kwargs["individual_id"] = self.convert_individual_id(
                kwargs["family_id"], kwargs["individual_id"])
            kwargs["status"] = self.convert_status(kwargs["status"])
            kwargs["role"] = self.convert_role(kwargs["role"])
            kwargs["sex"] = self.convert_sex(kwargs["sex"])

            individuals.append(Individual(**kwargs))

        return self.read_structure(individuals)

    def read_filename(self, filename):
        with open(filename, "r") as csv_file:
            families = self.read_csv_file(csv_file)

        return families


class SPARKCsvIndividualsReader(CsvIndividualsReader):

    @property
    def FIELDS_TO_COLUMNS(self):
        return {
            "role": "role",
            "family_id": "family_id",
            "individual_id": "subject_sp_id",
            "sex": "sex",
            "status": "asd"
        }

    STATUS_TO_ENUM = {
        "True": Status.affected,
        "False": Status.unaffected
    }

    SEX_TO_ENUM = {
        "Male": Sex.male,
        "Female": Sex.female
    }

    def convert_status(self, status):
        return self.STATUS_TO_ENUM[status]

    def convert_sex(self, sex):
        return self.SEX_TO_ENUM[sex]

    def convert_individual_id(self, family_id, individual_id):
        return individual_id

    def convert_role(self, role):
        return RoleMapping.SPARK[role] \
            if role in RoleMapping.SPARK else Role.unknown


class InternalCsvIndividualsReader(CsvIndividualsReader):

    @property
    def FIELDS_TO_COLUMNS(self):
        return {
            "role": "role",
            "family_id": "family_id",
            "individual_id": "individual_id",
            "sex": "sex",
            "status": "affected"
        }

    STATUS_TO_ENUM = {
        "True": Status.affected,
        "False": Status.unaffected
    }

    SEX_TO_ENUM = {
        "Male": Sex.male,
        "Female": Sex.female
    }

    def convert_status(self, status):
        return self.STATUS_TO_ENUM[status]

    def convert_sex(self, sex):
        return self.SEX_TO_ENUM[sex]

    def convert_individual_id(self, family_id, individual_id):
        return individual_id

    def convert_role(self, role):
        return RoleMapping.INTERNAL[role] \
            if role in RoleMapping.INTERNAL else Role.unknown


class VIPCsvIndividualsReader(CsvIndividualsReader):

    @property
    def FIELDS_TO_COLUMNS(self):
        return {
            "role": "relationship_to_iip",
            "family_id": "family",
            "individual_id": "sfari_id",
            "sex": "sex",
            # "status": "genetic_status",
            "status": "genetic_status_16p",
        }

    SEX_TO_ENUM = {
        "Male": Sex.male,
        "Female": Sex.female
    }

    def convert_family_id(self, family_id):
        return family_id.split("-")[0]

    def convert_individual_id(self, family_id, individual_id):
        return individual_id

    def convert_role(self, role):
        return RoleMapping.VIP[role] \
            if role in RoleMapping.VIP else Role.unknown

    def convert_sex(self, sex):
        return self.SEX_TO_ENUM[sex]

    def convert_status(self, status):
        return Status.unaffected if status == 'negative' \
            else Status.affected
#         return Status.unaffected if status == 'Negative (normal)' \
#             else Status.affected


class FamilyToPedigree(object):

    AMBIGUOUS_ROLES = [
        Role.maternal_cousin, Role.paternal_cousin,
        Role.maternal_half_sibling, Role.paternal_half_sibling
    ]

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

        if role == Role.paternal_cousin:
            return IndividualUnit()

        if role == Role.maternal_cousin:
            return IndividualUnit()

        if role == Role.unknown:
            return IndividualUnit()

        raise NotImplementedError("Unknown individual role: {}".format(role))

    def print_ambiguous_warning(self, individual, verbose=True):
        if verbose and individual.role in self.AMBIGUOUS_ROLES:
            msg = "family {} (person {}) with ambiguous role: {}\n".format(
                individual.family_id,
                individual.individual_id,
                individual.role)
            sys.stderr.write(msg)

    def assert_propper_family(self, family_members):
        assert len(family_members) != 0, "No members for family"

        family_name = family_members[0].family_id

        moms = [fm for fm in family_members if fm.role == Role.mom]
        moms_count = len(moms)
        assert moms_count < 2, \
            "{}: {} moms - {}".format(family_name, moms_count, moms)

        dads = [fm for fm in family_members if fm.role == Role.dad]
        dads_count = len(dads)
        assert dads_count < 2, \
            "{}: {} dads - {}".format(family_name, dads_count, dads)

        probands = [fm for fm in family_members if fm.role == Role.prb]
        probands_count = len(probands)
        assert probands_count < 2, \
            "{}: {} probands - {}".format(family_name,
                                          probands_count, probands)

    def to_pedigree(self, family_members):
        self.assert_propper_family(family_members)

        individual_id_to_individual_unit = OrderedDict()
        probands = [individual for individual in family_members
                    if individual.role == Role.prb]
        other = [individual for individual in family_members
                 if individual.role != Role.prb]

        proband_unit = IndividualUnit()
        if len(probands) == 1:
            proband = probands[0]
            proband_unit.individual = proband

            individual_id_to_individual_unit[proband.individual_id] = \
                proband_unit

        for individual in other:
            self.print_ambiguous_warning(individual)
            individual_unit = self.get_individual(
                proband_unit, individual.role)
            individual_unit.individual = individual
            individual_id_to_individual_unit[individual.individual_id] = \
                individual_unit

        return list(individual_id_to_individual_unit.values())


class PedigreeToCsv(object):

    def __init__(self, filename):
        self.filename = filename

    def write_pedigrees(self, pedigrees):
        with open(self.filename, "w") as csv_file:
            writer = csv.writer(csv_file, delimiter='\t')
            writer.writerow([
                "familyId", "personId", "dadId", "momId", "sex",
                "status", "role"])
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
    parser.add_argument(
        "--output", dest="output", default="output.ped", type=str)
    parser.add_argument("--pheno", dest="pheno", type=str)
    args = parser.parse_args()

    reader = None
    if args.pheno == 'spark':
        reader = SPARKCsvIndividualsReader()

    assert reader is not None

    families = reader.read_filename(args.file)

    pedigrees = {}

    for family_name, members in list(families.items()):
        try:
            pedigree = FamilyToPedigree().to_pedigree(members)
            pedigrees[family_name] = pedigree
        except AssertionError as e:
            sys.stderr.write(
                "skipping {}; reason: {}\n".format(family_name, str(e)))

    pedigrees_list = list(itertools.chain(*list(pedigrees.values())))

    PedigreeToCsv(args.output).write_pedigrees(pedigrees_list)


if __name__ == "__main__":
    main()
