'''
Created on Mar 28, 2017

@author: lubo
'''
import traceback
import itertools
import pandas as pd
import numpy as np
from pheno.utils.configuration import PhenoConfig
from collections import OrderedDict, Counter
from pheno.models import PersonManager
from pheno.prepare.base_variables import BaseVariables
import os
from pheno.prepare.base_meta_variables import BaseMetaVariables
from pheno.pheno_db import PhenoDB


class NucPedPrepareIndividuals(PhenoConfig):

    class Family(object):

        def __init__(self, family_id):
            self.family_id = family_id
            self.mother = None
            self.father = None
            self.probands = OrderedDict()
            self.siblings = OrderedDict()

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
            assert mother is not None

            mother.role = 'mom'
            mother.role_id = mother.role
            mother.role_order = 0
            mother.family_id = self.family_id
            self.mother = mother

        def add_father(self, father):
            assert self.father is None
            assert father.role is None
            assert father.family_id is None
            assert father is not None

            father.role = 'dad'
            father.role_id = father.role
            father.role_order = 1
            father.family_id = self.family_id
            self.father = father

        def add_child(self, p):
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
            p.role_id = p.role
            p.role_order = len(self.probands) + 11
            p.family_id = self.family_id
            self.probands[p.person_id] = p

        def add_sibling(self, p):
            assert p.proband_sibling == 'sib'
            assert p.person_id not in self.siblings
            assert p.role is None
            assert p.family_id is None

            p.role = 'sib'
            p.role_id = p.role
            p.role_order = len(self.siblings) + 21
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
            self.father = row['dadId']
            self.mother = row['momId']
            self.person_id = row['personId']
            self.family = row['familyId']
            self.gender = self._build_gender(row['gender'])
            self.proband_sibling = self._build_proband_sibling(row['status'])
            self.sample_id = self._build_sample_id(row['sampleId'])
            self.role = None
            self.family_id = None
            self.collection = None
            self.ssc_present = None

            self.key = (self.family, self.person_id)
            assert self.person_id is not None

        def __eq__(self, other):
            return self.father == other.father and \
                self.mother == other.mother and \
                self.person_id == other.person_id and \
                self.gender == other.gender and \
                self.proband_sibling == other.proband_sibling and \
                self.family_id == other.family_id and \
                self.key == other.key and \
                self.sample_id == other.sample_id
            # self.role == other.role and \

        def __ne__(self, other):
            return not self.__eq__(other)

        def _build_sample_id(self, sample_id):
            if isinstance(sample_id, float) and np.isnan(sample_id):
                return None
            elif sample_id is None:
                return None

            return str(sample_id)

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
            else:
                print("unexpected status: {}".format(status))
                raise ValueError("unexpected value for status: {}"
                                 .format(status))

    def __init__(self, config, *args, **kwargs):
        super(NucPedPrepareIndividuals, self).__init__(
            pheno_db='output', config=config, *args, **kwargs)

    def _build_individuals_dict(self, df):
        individuals = {}
        for _index, row in df.iterrows():
            individual = NucPedPrepareIndividuals.Individual(row)

            if individual.key not in individuals:
                individuals[individual.key] = individual
            elif individuals[individual.key] != individual:
                print("---------------------------------------------")
                print("Mismatched individuals:")
                print(">\t{}".format(individual))
                print(">\t{}".format(individuals[individual.key]))
                print("---------------------------------------------")

        return individuals

    def load_pedfile(self, pedfilename):
        df = pd.read_csv(pedfilename, sep='\t')
        assert list(df.columns) == [
            'familyId', 'personId', 'dadId', 'momId',
            'gender', 'status', 'sampleId']
        return df

    def _build_individuals(self, pedfilename):
        df = self.load_pedfile(pedfilename)
        individuals = self._build_individuals_dict(df)
        assert individuals is not None

        families = self._build_families_dict(individuals)
        assert families is not None

        return individuals

    def build(self, pedfilename):
        self.individuals = self._build_individuals(pedfilename)
        self.individuals_with_sample_id = {
            k: v for k, v in self.individuals.items()
            if v.sample_id is not None
        }

    def _build_families_dict(self, individuals):
        families = {}
        for p in individuals.values():
            if p.father != '0' and p.mother != '0':
                try:
                    father = individuals[(p.family, p.father)]
                    mother = individuals[(p.family, p.mother)]

                    assert father is not None
                    assert mother is not None

                    family_id = "{mom}-{dad}".format(
                        mom=mother.person_id, dad=father.person_id)
                    if family_id in families:
                        family = families[family_id]
                    else:
                        family = NucPedPrepareIndividuals.Family(family_id)
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

    def save(self):
        with PersonManager(pheno_db=self.pheno_db, config=self.config) as pm:
            pm.drop_tables()
            pm.create_tables()
            for p in self.individuals.values():
                pm.save(p)

    def prepare(self, pedfilename):
        self.build(pedfilename)
        self.save()


class NucPedPrepareVariables(PhenoConfig, BaseVariables):

    def __init__(self, config, *args, **kwargs):
        super(NucPedPrepareVariables, self).__init__(
            pheno_db='output', config=config, *args, **kwargs)

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

    def _adjust_measurments_with_sample_id(self, df, individuals):
        to_append = []
        for individual in individuals.individuals_with_sample_id.values():
            pdf = df[df.person_id == individual.sample_id]
            assert len(pdf) == 1
            adf = pdf.copy()
            adf.person_id = individual.person_id

            to_append.append(adf)
            print(adf.person_id)

        return df.append(to_append)

    def load_instrument(
            self, individuals, instrument_name, filename, dtype=None):

        print("processing table: {}".format(filename))
        assert os.path.isfile(filename)

        df = pd.read_csv(filename, low_memory=False, sep=',',
                         na_values=[' '], dtype=dtype)
        columns = [c for c in df.columns]
        columns[0] = 'person_id'

        for index in range(1, len(columns)):
            parts = columns[index].split('.')
            parts = [p for p in parts if p.strip() != instrument_name.strip()]
            if len(parts) == 1:
                name = parts[0]
            else:
                name = '.'.join(parts[1:])
            columns[index] = name

        df.columns = columns
        self._clear_duplicate_measurements(df)
        df = self._adjust_measurments_with_sample_id(df, individuals)
        return df

    def prepare(self, pedindividuals, instruments_directory):
        self._create_variable_table()
        self._create_value_tables()

        persons = self.load_persons_df()

        all_filenames = [
            os.path.join(instruments_directory, f)
            for f in os.listdir(instruments_directory)
            if os.path.isfile(os.path.join(instruments_directory, f))]
        print(all_filenames)
        for filename in all_filenames:
            basename = os.path.basename(filename)
            instrument_name, ext = os.path.splitext(basename)
            print(basename)
            print(instrument_name, ext)
            if ext != '.csv':
                continue
            instrument_df = self.load_instrument(
                pedindividuals, instrument_name, filename)

            df = instrument_df.join(
                persons, on='person_id', how='right', rsuffix="_person")

            for measure_name in df.columns[1:len(instrument_df.columns)]:
                mdf = df[['person_id', measure_name,
                          'family_id', 'person_role']]
                self._build_variable(instrument_name, measure_name,
                                     mdf.dropna())


class NucPedPrepareMetaVariables(PhenoConfig, BaseMetaVariables):

    def __init__(self, config, *args, **kwargs):
        super(NucPedPrepareMetaVariables, self).__init__(
            pheno_db='output', config=config, *args, **kwargs)
        self.phdb = PhenoDB(self.pheno_db, config=config)
        self.phdb.load()
