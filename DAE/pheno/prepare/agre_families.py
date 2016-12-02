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


class AgreLoader(PhenoConfig):

    INDIVIDUALS = 'AGRE_Pedigree_Catalog_10-05-2012.csv'

    def __init__(self, *args, **kwargs):
        super(AgreLoader, self).__init__(*args, **kwargs)

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

    def _clean_individuals_dict(self, families):
        families = self._clean_families_without_probands(families)
        individuals = OrderedDict()
        for family in families.values():
            print(family)
            assert family.mother.person_id not in individuals
            assert family.father.person_id not in individuals

            individuals[family.mother.person_id] = family.mother
            individuals[family.father.person_id] = family.father
            family.mother.role_order = 0
            family.father.role_order = 1
            for order, p in enumerate(family.probands.values()):
                assert p.person_id not in individuals
                p.role_order = 20 + order
                individuals[p.person_id] = p

            for order, p in enumerate(family.siblings.values()):
                assert p.person_id not in individuals
                p.role_order = 30 + order
                individuals[p.person_id] = p
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
        print(p)
        person_id = p.person_id
        family_id = p.family_id
        role = p.role
        role_id = p.role
        role_order = p.role_order

        t = [person_id, family_id, role_id,
             role, role_order, ]
        return tuple(t)

#     def _build_role(self, row):
#         if row['Person'] == 1:
#             role = 'mo'
#             role_type = 'mom'
#             assert row['Sex'] == 'Female'
#         elif row['Person'] == 2:
#             role = 'fa'
#             role_type = 'dad'
#             assert row['Sex'] == 'Male'
#         elif row['Scored Affected Status'] != '':
#             role = 'p'
#             role_type = 'prb'
#         else:
#             role = 's'
#             role_type = 'sib'
#         return role, role_type
#
