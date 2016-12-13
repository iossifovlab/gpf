'''
Created on Dec 13, 2016

@author: lubo
'''
from collections import Counter, OrderedDict
import copy
import os

import pandas as pd
from pheno.utils.configuration import PhenoConfig
import traceback
import itertools
from pheno.models import PersonManager, PersonModel


class VipLoader(PhenoConfig):

    INDIVIDUALS = 'svip.csv'
    SUBDIR = "SVIP_16p11.2"

    def __init__(self, *args, **kwargs):
        super(VipLoader, self).__init__(pheno_db='vip', *args, **kwargs)

    def _clear_duplicate_measurements(self, df):
        counter = Counter(df.person_id)
        to_fix = [k for k, v in counter.items() if v > 1]
        to_delete = []
        for person_id in to_fix:
            print("fixing measurements for {}".format(person_id))
            pdf = df[df.person_id == person_id]
            keep = pdf.age.idxmax()
            d = pdf[pdf.index != keep]
            to_delete.extend(d.index.values)

        df.drop(to_delete, inplace=True)

    def load_instrument(self, instrument_name, dtype=None):
        dirname = self.config.get('vip', 'dir')
        assert os.path.isdir(dirname)

        filename = os.path.join(
            dirname,
            self.SUBDIR,
            "{}.csv".format(instrument_name))
        assert os.path.isfile(filename)
        print("processing table: {}".format(filename))

        df = pd.read_csv(filename, low_memory=False, sep=',',
                         na_values=[' '], dtype=dtype)
        columns = [c for c in df.columns]
        columns[0] = 'person_id'
        columns[5] = 'age'
        for index in range(6, len(columns)):
            parts = columns[index].split('.')
            name = '.'.join(parts[1:])
            columns[index] = name
        df.columns = columns
        self._clear_duplicate_measurements(df)
        return df

    def _load_df(self, name, sep='\t', dtype=None):
        filename = os.path.join(self.config.get('vip', 'dir'), name)
        assert os.path.isfile(filename)
        df = pd.read_csv(filename, low_memory=False, sep=sep,
                         na_values=[' '],
                         true_values=['yes', 'true', 'True'],
                         false_values=['no', 'false', 'False'],
                         dtype=dtype)

        return df

    def load_individuals(self):
        df = self._load_df(self.INDIVIDUALS, sep=',')
        return df


class PrepareIndividuals(VipLoader):

    class Family(object):

        def __init__(self, family_id):
            self.family_id = family_id
            self.mother = None
            self.father = None
            self.probands = {}
            self.siblings = {}

        @property
        def size(self):
            return 2 + len(self.probands) + len(self.siblings)

        def __repr__(self):
            return "Family({family_id}, {mother}, {father}, " \
                "{probands}, {siblings})".format(
                    family_id=self.family_id,
                    mother=self.mother,
                    father=self.father,
                    probands=self.probands,
                    siblings=self.siblings)

        def add_mother(self, mother):
            assert self.mother is None
            assert mother.role is None
            assert mother.family_id is None
            mother = copy.deepcopy(mother)
            assert mother is not None

            mother.role = 'mom'
            mother.family_id = self.family_id
            self.mother = mother

        def add_father(self, father):
            assert self.father is None
            assert father.role is None
            assert father.family_id is None
            father = copy.deepcopy(father)
            assert father is not None

            father.role = 'dad'
            father.family_id = self.family_id
            self.father = father

        def add_child(self, p):
            p = copy.deepcopy(p)
            if p.proband_sibling == 'prb':
                self.add_proband(p)
            elif p.proband_sibling == 'sib':
                self.add_sibling(p)

        def add_proband(self, p):
            assert p.proband_sibling == 'prb'
            assert p.person_id not in self.probands
            assert p.role is None
            assert p.family_id is None

            p.role = 'prb'
            p.family_id = self.family_id
            self.probands[p.person_id] = p

        def add_sibling(self, p):
            assert p.proband_sibling == 'sib'
            assert p.person_id not in self.siblings
            assert p.role is None
            assert p.family_id is None

            p.role = 'sib'
            p.family_id = self.family_id
            self.siblings[p.person_id] = p

    class Individual(object):

        def __repr__(self):
            return "Individual({person_id}, {gender}, {role}, {family_id}, " \
                "{father}, {mother})" \
                .format(
                    person_id=self.person_id,
                    gender=self.gender,
                    role=self.role,
                    family_id=self.family_id,
                    father=self.father,
                    mother=self.mother,
                )

        def __init__(self, row):
            self.father = row['father']
            self.mother = row['mother']
            self.person_id = row['person_id']
            self.family = row['family']
            self.gender = self._build_gender(row['gender'])
            self.proband_sibling = self._build_proband_sibling(row['prb/sib'])
            self.role = None
            self.family_id = None

            self.key = (self.family, self.person_id)
            assert self.person_id is not None

        def __eq__(self, other):
            return self.father == other.father and \
                self.mother == other.mother and \
                self.person_id == other.person_id and \
                self.gender == other.gender and \
                self.proband_sibling == other.proband_sibling and \
                self.family_id == other.family_id and \
                self.key == other.key
            # self.role == other.role and \

        def __ne__(self, other):
            return not self.__eq__(other)

        @staticmethod
        def _build_family_id(person_id):
            parts = person_id.split('.')
            assert len(parts) == 2
            return parts[0]

        @staticmethod
        def _build_gender(sex):
            if sex == 1:
                return 'M'
            elif sex == 2:
                return 'F'
            else:
                raise ValueError("unexpected value for gender: {}"
                                 .format(sex))

        @staticmethod
        def _build_proband_sibling(status):
            if status == 1:
                return 'sib'
            elif status == 2:
                return 'prb'
            elif status == 0:
                print("unknown status")
                return 'sib'
            else:
                print("unexpected status: {}".format(status))
                raise ValueError("unexpected value for role: {}"
                                 .format(status))

    def _build_individuals_dict(self, df):
        individuals = {}
        for _index, row in df.iterrows():
            individual = PrepareIndividuals.Individual(row)

            if individual.key not in individuals:
                individuals[individual.key] = individual
            elif individuals[individual.key] != individual:
                print("---------------------------------------------")
                print("Mismatched individuals:")
                print(">\t{}".format(individual))
                print(">\t{}".format(individuals[individual.key]))
                print("---------------------------------------------")

        return individuals

    def _build_individuals(self):
        df = self.load_individuals()
        individuals = self._build_individuals_dict(df)
        assert individuals is not None

        families = self._build_families_dict(individuals)
        assert families is not None

        individuals = self._clean_individuals_dict(families)
        assert individuals is not None

        return individuals

    def _build_families_dict(self, individuals):
        families = {}
        for p in individuals.values():
            if p.father != '0' and p.mother != '0':
                try:
                    father = individuals[(p.family, p.father)]
                    mother = individuals[(p.family, p.mother)]

                    assert father is not None
                    assert mother is not None

                    family_id = "{mom}_{dad}".format(
                        mom=mother.person_id, dad=father.person_id)
                    if family_id in families:
                        family = families[family_id]
                    else:
                        family = PrepareIndividuals.Family(family_id)
                        family.add_mother(mother)
                        family.add_father(father)

                    family.add_child(p)
                    families[family_id] = family
                    assert family.father is not None
                    assert family.mother is not None

                except AssertionError:
                    print("----------------------------------------------")
                    print("Problem creating family: {}".format(family_id))
                    traceback.print_exc()
                    print("\tmother: {}".format(mother))
                    print("\tfather: {}".format(father))
                    print("\tchild:  {}".format(p))
                    print("----------------------------------------------")

        return families

    def _clean_families_without_probands(self, families):
        result = {}
        for family in families.values():
            if family.probands:
                result[family.family_id] = family
            else:
                print("----------------------------")
                print("family without probands: {}".format(
                    family.family_id))
        assert len(result) > 1
        print("----------------------------------------------")
        print("ALL:   {}".format(len(families)))
        print("CLEAN: {}".format(len(result)))
        print("----------------------------------------------")
        return result

    def _add_family(self, fam, individuals):
        for order, p in enumerate(itertools.chain([fam.mother], [fam.father],
                                                  fam.probands.values(),
                                                  fam.siblings.values())):
            if p.person_id in individuals:
                # conflicting person:
                other_person = individuals[p.person_id]
                # print("CONFLICTING PERSON: {} <-> {}".format(
                # p, other_person))
                return other_person
            p.role_order = order
            individuals[p.person_id] = p

    def _clean_individuals_dict(self, families):
        families = self._clean_families_without_probands(families)
        individuals = OrderedDict()
        for family in families.values():
            conflict = self._add_family(family, individuals)
            if conflict:
                other_family = families[conflict.family_id]
                self._resolve_family_conflict(
                    family, other_family, individuals)
        assert len(individuals) > 0
        return individuals

    def prepare(self):
        individuals = self._build_individuals()
        with PersonManager(pheno_db=self.pheno_db, config=self.config) as pm:
            pm.drop_tables()
            pm.create_tables()

            for count, person in enumerate(individuals.values()):
                p = PersonModel()
                p.person_id = person.person_id
                p.family_id = person.family_id
                p.role = person.role
                p.role_id = person.role
                p.role_order = count
                p.gender = person.gender
                p.race = None
                p.collection = 'vip'
                p.ssc_present = 1

                pm.save(p)

    @property
    def person_manager(self):
        return PersonManager(pheno_db='vip', config=self.config)
