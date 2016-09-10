'''
Created on Aug 25, 2016

@author: lubo
'''
import numpy as np
import pandas as pd
from pheno.models import PersonManager, PersonModel, RawValueManager,\
    ContinuousValueManager, ContinuousValueModel
from pheno.utils.load_raw import V15Loader, V14Loader


class PrepareIndividuals(V15Loader):

    def __init__(self, *args, **kwargs):
        super(PrepareIndividuals, self).__init__(*args, **kwargs)

    @staticmethod
    def _role_order(role):
        if role == 'mo':
            return 0
        elif role == 'fa':
            return 10
        elif role[0] == 'p':
            return 20 + int(role[1])
        elif role[0] == 's' or role[0] == 'x':
            return 30 + int(role[1])
        else:
            raise ValueError("unexpected role: {}".format(role))

    @staticmethod
    def _role_type(role):
        if role == 'mo':
            return 'mom'
        elif role == 'fa':
            return 'dad'
        elif role[0] == 'p':
            return 'prb'
        elif role[0] == 's' or role[0] == 'x':
            return 'sib'

    def _build_individuals_dtype(self):
        dtype = [('personId', 'S16'), ('familyId', 'S16'),
                 ('roleId', 'S8'), ('role', 'S8'),
                 ('roleOrder', int), ('collection', 'S64')]
        return dtype

    def _build_individuals_row(self, row):
        person_id = row['SSC ID']
        collection = row['Collection']
        [family_id, role_id] = person_id.split('.')
        role_order = self._role_order(role_id)
        role_type = self._role_type(role_id)
        t = [person_id, family_id, role_id,
             role_type, role_order, collection]
        return tuple(t)

    def _build_df_from_individuals(self):
        individuals = self.load_individuals()
        dtype = self._build_individuals_dtype()

        values = []
        for _index, row in individuals.iterrows():
            t = self._build_individuals_row(row)
            values.append(t)

        persons = np.array(values, dtype)
        persons = np.sort(persons, order=['familyId', 'roleOrder'])
        df = pd.DataFrame(persons)

        return df

    def prepare(self):
        df = self._build_df_from_individuals()
        with PersonManager(config=self.config) as pm:
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
                p.collection = None if (isinstance(row['collection'], float) or
                                        row['collection'] == 'nan') \
                    else row['collection']
                p.ssc_present = None

                pm.save(p)


class PrepareIndividualsGender(V15Loader):

    def __init__(self, *args, **kwargs):
        super(PrepareIndividualsGender, self).__init__(*args, **kwargs)

    def _build_proband_gender(self, df):
        [cd] = self.load_table('ssc_core_descriptive', roles=['prb'])
        for _index, row in cd.iterrows():
            pid = row['individual']
            gender = row['sex'].upper()[0]
            df.loc[df.person_id == pid, 'gender'] = gender
        return df

    def _build_siblings_gender(self, df):
        cds = self.load_table('ssc_core_descriptive', roles=['sib'])
        for cd in cds:
            for _index, row in cd.iterrows():
                pid = row['individual']
                if isinstance(row['sex'], float):
                    gender = None
                else:
                    gender = row['sex'].upper()[0]
                df.loc[df.person_id == pid, 'gender'] = gender
        return df

    def _build_gender(self, df):
        gender = df['gender']

        gender[df.role == 'mom'] = 'F'
        gender[df.role == 'dad'] = 'M'

        df = self._build_proband_gender(df)
        df = self._build_siblings_gender(df)

        return df

    def prepare(self):
        with PersonManager(config=self.config) as pm:
            df = pm.load_df()
            self._build_gender(df)
            pm.save_df(df)


class PrepareIndividualsSSCPresent(V15Loader):

    def __init__(self, *args, **kwargs):
        super(PrepareIndividualsSSCPresent, self).__init__(*args, **kwargs)

    def _build_ssc_present(self, df):
        persons = {}
        for _index, val in df.person_id.iteritems():
            persons[val] = []

        for st in self.get_all_ssc_studies():
            print("processing study: {}".format(st.name))
            for _fid, fam in st.families.items():
                for p in fam.memberInOrder:
                    if p.personId not in persons:
                        print("person: {} from study: {} not found in PhenoDB"
                              .format(p.personId, st.name))
                        continue
                    persons[p.personId].append((st.name, p))

        missing = []
        for pid, studies in persons.items():
            if len(studies) == 0:
                missing.append(pid)

        df.ssc_present = True

        missing.sort()
        for pid in missing:
            df.loc[df.person_id == pid, 'ssc_present'] = False
        return df

    def prepare(self):
        with PersonManager(config=self.config) as pm:
            df = pm.load_df()
            self._build_ssc_present(df)
            pm.save_df(df)


class PrepareIndividualsGenderFromSSC(V15Loader):

    def __init__(self, *args, **kwargs):
        super(PrepareIndividualsGenderFromSSC, self).__init__(*args, **kwargs)

    def _build_gender_from_ssc(self, df):
        persons = {}
        for _index, val in df.person_id.iteritems():
            persons[val] = []

        for st in self.get_all_ssc_studies():
            print("processing study: {}".format(st.name))
            for _fid, fam in st.families.items():
                for p in fam.memberInOrder:
                    if p.personId in persons:
                        p.study = st.name
                        persons[p.personId].append(p)

        gender = {}
        for pid, ps in persons.items():
            assert len(ps) > 0
            if len(ps) == 1:
                gender[pid] = ps[0].gender
            else:
                check = [p.gender == ps[0].gender for p in ps]
                if all(check):
                    gender[pid] = ps[0].gender
                else:
                    print("\ngender mismatch for person: {}:".format(pid))
                    for p in ps:
                        print("\tstudy: {}; pid: {}; gender {}".format(
                            p.study, p.personId, p.gender))

        for pid, gender in gender.items():
            df.loc[df.person_id == pid, 'gender'] = gender
        return df

    def prepare(self):
        with PersonManager(config=self.config) as pm:
            df = pm.load_df(where='gender is null and ssc_present=1')
            self._build_gender_from_ssc(df)

            pm.save_df(df)


class PrepareIndividualsAge(V14Loader):

    def __init__(self, *args, **kwargs):
        super(PrepareIndividualsAge, self).__init__(*args, **kwargs)

    def prepare(self):
        df = self.load_df('ssc_age_at_assessment.csv')
        with PersonManager(config=self.config) as pm:
            for _index, row in df.iterrows():
                pid = row['portalId']
                person = pm.get("person_id = '{}'".format(pid))
                person.age = int(row['age_at_assessment'])
                person.site = row['site']
                pm.save(person)


class PrepareIndividualsRace(V15Loader):

    def __init__(self, *args, **kwargs):
        super(PrepareIndividualsRace, self).__init__(*args, **kwargs)

    def _prepare_probands_race(self):
        with RawValueManager(config=self.config) as vm:
            df = vm.load_df(
                where="variable_id='{}'"
                .format('ssc_core_descriptive.race'))
        with PersonManager(config=self.config) as pm:
            # print('setting race for {}'.format(row['person_id']))
            for _index, row in df.iterrows():
                person = pm.get(
                    where="person_id='{}'".format(row['person_id']))
                person.race = row['value']
                pm.save(person)

    def _prepare_parents_race(self):
        with RawValueManager(config=self.config) as vm:
            df = vm.load_df(
                where="variable_id='{}'"
                .format('ssc_commonly_used.race_parents'))
        with PersonManager(config=self.config) as pm:
            # print('setting race for {}'.format(row['person_id']))
            for _index, row in df.iterrows():
                person = pm.get("person_id='{}'".format(row['person_id']))
                person.race = row['value']
                pm.save(person)

    def _prepare_siblings_race(self):
        with PersonManager(config=self.config) as pm:
            siblings = pm.load_df(where="role='sib'")
            for _index, row in siblings.iterrows():
                sib = PersonModel.create_from_df(row)
                mom = pm.get(where="person_id='{}.mo'".format(sib.family_id))
                dad = pm.get(where="person_id='{}.fa'".format(sib.family_id))
                sib.race = PersonModel.calc_race(mom.race, dad.race)
                pm.save(sib)

    def _check_probands_race(self):
        with PersonManager(config=self.config) as pm:
            probands = pm.load_df(where="role='prb'")
            for _index, row in probands.iterrows():
                prb = PersonModel.create_from_df(row)
                mom = pm.get(where="person_id='{}.mo'".format(prb.family_id))
                dad = pm.get(where="person_id='{}.fa'".format(prb.family_id))
                race = PersonModel.calc_race(mom.race, dad.race)
                if prb.race != race:
                    print("family: {}; prb: |{}|; mom: |{}|; dad: |{}|".format(
                        prb.family_id, prb.race, mom.race, dad.race))

    def prepare(self):
        self._prepare_probands_race()
        self._prepare_parents_race()
        self._prepare_siblings_race()
        self._check_probands_race()


class PrepareNonverbalIQ(V15Loader):
    NONVERBAL_IQ = 'ssc_core_descriptive.ssc_diagnosis_nonverbal_iq'
    VERBAL_IQ = 'ssc_core_descriptive.ssc_diagnosis_verbal_iq'

    def _prepare_nonverbal_iq(self):
        with ContinuousValueManager(config=self.config) as vm:
            df = vm.load_df(where="variable_id='{}'".format(self.NONVERBAL_IQ))

        with PersonManager(config=self.config) as pm:
            for _index, row in df.iterrows():
                val = ContinuousValueModel.create_from_df(row)
                person = pm.get(where="person_id='{}'".format(val.person_id))
                person.non_verbal_iq = val.value
                pm.save(person)

    def _prepare_verbal_iq(self):
        with ContinuousValueManager(config=self.config) as vm:
            df = vm.load_df(where="variable_id='{}'".format(self.VERBAL_IQ))

        with PersonManager(config=self.config) as pm:
            for _index, row in df.iterrows():
                val = ContinuousValueModel.create_from_df(row)
                person = pm.get(where="person_id='{}'".format(val.person_id))
                person.verbal_iq = val.value
                pm.save(person)

    def prepare(self):
        self._prepare_nonverbal_iq()
        self._prepare_verbal_iq()


class CheckIndividualsGenderToSSC(V15Loader):

    def __init__(self, *args, **kwargs):
        super(CheckIndividualsGenderToSSC, self).__init__(*args, **kwargs)

    def _check_gender_to_ssc(self, df):
        persons = {}
        for _index, val in df.person_id.iteritems():
            persons[val] = []

        for st in self.get_all_ssc_studies():
            print("processing study: {}".format(st.name))
            for _fid, fam in st.families.items():
                for p in fam.memberInOrder:
                    if p.personId in persons:
                        p.study = st.name
                        persons[p.personId].append(p)

        gender = {}
        for pid, ps in persons.items():
            assert len(ps) > 0
            if len(ps) == 1:
                gender[pid] = ps[0].gender
            else:
                check = [p.gender == ps[0].gender for p in ps]
                if all(check):
                    gender[pid] = ps[0].gender
                else:
                    print("\ngender mismatch for person: {}:".format(pid))
                    for p in ps:
                        print("\tstudy: {}; pid: {}; gender {}".format(
                            p.study, p.personId, p.gender))

            check = df[df.person_id == pid].gender == gender[pid]
            if not np.all(check):
                print("\ngender mismatch for person: {}".format(pid))
                print("\tpheno db gender: {}".format(
                    df[df.person_id == pid].gender.values))
                for p in ps:
                    print("\tstudy: {}; pid: {}; gender {}".format(
                        p.study, p.personId, p.gender))

    def check(self):
        with PersonManager(config=self.config) as pm:
            df = pm.load_df(where='ssc_present=1')
            self._check_gender_to_ssc(df)
