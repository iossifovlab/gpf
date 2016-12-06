'''
Created on Nov 29, 2016

@author: lubo
'''
from pheno.utils.configuration import PhenoConfig
import os

import pandas as pd
import numpy as np
import copy
from collections import OrderedDict
import itertools
from pheno.models import PersonManager, PersonModel


class AgreLoader(PhenoConfig):

    INDIVIDUALS = 'AGRE_Pedigree_Catalog_10-05-2012.csv'

    def __init__(self, *args, **kwargs):
        super(AgreLoader, self).__init__(pheno_db='agre', *args, **kwargs)

    def load_table(self, table_name, roles=['prb'], dtype=None):
        result = []
        for data_dir in self._data_dirs(roles):
            dirname = os.path.join(self['agre', 'dir'], data_dir)
            assert os.path.isdir(dirname)

            filename = os.path.join(dirname, "{}.csv".format(table_name))
            if not os.path.isfile(filename):
                print("skipping {}...".format(filename))
                continue

            print("processing table: {}".format(filename))

            df = pd.read_csv(filename, low_memory=False, dtype=dtype)
            result.append(df)

        return result

    def _load_df(self, name, sep='\t', dtype=None):
        filename = os.path.join(self['agre', 'dir'], name)
        assert os.path.isfile(filename)
        df = pd.read_csv(filename, low_memory=False, sep=sep, dtype=dtype)

        return df

    def load_individuals(self):
        df = self._load_df(self.INDIVIDUALS)
        return df


class PrepareIndividuals(AgreLoader):

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
            return "Individual({person_id}, {gender}, {role}, {family_id})" \
                .format(
                    person_id=self.person_id,
                    gender=self.gender,
                    role=self.role,
                    family_id=self.family_id
                )

        def __init__(self, row):
            self.au = row['AU']
            self.person = row['Person']
            self.father = row['Father']
            self.mother = row['Mother']
            self.individual_code = row['Individual Code']
            self.person_id = self.individual_code
            self.gender = self._build_gender(row['Sex'])
            self.proband_sibling = self._build_proband_sibling(
                row['Scored Affected Status'])
            self.role = None
            self.family_id = None

            self.key = (self.au, self.person)
            assert self.person_id is not None

        @staticmethod
        def _build_gender(sex):
            if sex.lower() == 'male':
                return 'M'
            elif sex.lower() == 'female':
                return 'F'
            else:
                raise ValueError("unexpected value for gender: {}"
                                 .format(sex))

        @staticmethod
        def _build_proband_sibling(status):
            if status == 'Autism' or \
                    status == 'BroadSpectrum' or \
                    status == 'NQA' or \
                    status == 'ASD'or \
                    status == 'PDD-NOS':
                return 'prb'
            elif isinstance(status, float) and np.isnan(status):
                return 'sib'
            elif status == 'Not Met':
                return 'sib'
            else:
                print(type(status))
                raise ValueError("unexpected value for role: {}"
                                 .format(status))

    def __init__(self, *args, **kwargs):
        super(PrepareIndividuals, self).__init__(*args, **kwargs)

    def _build_individual(self, row):
        return PrepareIndividuals.Individual(row)

    def _build_individuals_df(self):
        df = self.load_individuals()
        individuals = self._build_individuals_dict(df)
        assert individuals is not None

        families = self._build_families_dict(individuals)
        assert families is not None

        individuals = self._clean_individuals_dict(families)
        assert individuals is not None

        df = self._build_df_from_individuals_dict(individuals)
        return df

    def _build_individuals_dict(self, df):
        individuals = {}
        for _index, row in df.iterrows():
            individual = self._build_individual(row)
            individuals[individual.key] = individual

        return individuals

    def _build_families_dict(self, individuals):
        families = {}
        for p in individuals.values():
            if p.father != 0 and p.mother != 0:
                try:

                    father = individuals[(p.au, p.father)]
                    mother = individuals[(p.au, p.mother)]

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
                    print("Problem creating family: {}".format(family_id))
                    print("\tmother: {}".format(mother))
                    print("\tfather: {}".format(father))
                    print("\tchild:  {}".format(p))

        return families

    def _clean_families_without_probands(self, families):
        result = {}
        for f in families.values():
            if f.probands:
                result[f.family_id] = f
        assert len(result) > 1
        return result

    def _resolve_family_conflict(self, fam1, fam2, individuals):
        self._remove_family(fam1, individuals)
        self._remove_family(fam2, individuals)
        print("conflicting families:\n\t{}\n<->\n\t{}".format(fam1, fam2))
        if fam1.size >= fam2.size:
            print("\tadding {}".format(fam1))
            self._add_family(fam1, individuals)
        else:
            self._add_family(fam2, individuals)
            print("\tadding {}".format(fam2))

    def _remove_family(self, fam, individuals):
        for p in itertools.chain([fam.mother], [fam.father],
                                 fam.probands.values(),
                                 fam.siblings.values()):
            if p.person_id in individuals:
                del individuals[p.person_id]

    def _add_family(self, fam, individuals):
        for order, p in enumerate(itertools.chain([fam.mother], [fam.father],
                                                  fam.probands.values(),
                                                  fam.siblings.values())):
            if p.person_id in individuals:
                # conflicting person:
                other_person = individuals[p.person_id]
                print("CONFLICTING PERSON: {} <-> {}".format(p, other_person))
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

    def _build_df_from_individuals_dict(self, individuals):
        dtype = self._build_individuals_dtype()

        values = []
        for individual in individuals.values():
            t = self._build_individuals_row(individual)
            values.append(t)

        persons = np.array(values, dtype)
        persons = np.sort(persons, order=['familyId', 'roleOrder'])
        df = pd.DataFrame(persons)

        return df

    def _build_individuals_dtype(self):
        dtype = [('personId', 'S16'), ('familyId', 'S16'),
                 ('roleId', 'S8'), ('role', 'S8'),
                 ('roleOrder', int), ]
        return dtype

    def _build_individuals_row(self, p):
        person_id = p.person_id
        family_id = p.family_id
        role = p.role
        role_id = p.role
        role_order = p.role_order

        t = [person_id, family_id, role_id,
             role, role_order, ]
        return tuple(t)

    def prepare(self):
        df = self._build_individuals_df()
        with PersonManager(pheno_db='agre', config=self.config) as pm:
            pm.drop_tables()
            pm.create_tables()

            for _index, row in df.iterrows():
                p = PersonModel()
                p.person_id = row['personId']
                p.family_id = row['familyId']
                p.role = row['role']
                p.role_id = row['roleId']
                p.role_order = row['roleOrder']
                p.gender = None
                p.race = None
                p.collection = 'agre'
                p.ssc_present = None

                pm.save(p)

    @property
    def person_manager(self):
        return PersonManager(config=self.config)
