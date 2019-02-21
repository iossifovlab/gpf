'''
Created on Feb 13, 2018

@author: lubo
'''
from __future__ import print_function
from __future__ import unicode_literals

from builtins import object
import numpy as np
import pandas as pd
from variants.attributes import Role, Sex, Status


class Person(object):

    def __init__(self, atts=None):
        if atts:
            self.atts = atts
        else:
            self.atts = {}
        assert 'person_id' in atts
        self.family_id = atts['family_id']
        self.person_id = atts['person_id']
        self.sample_id = atts.get('sample_id', None)
        self.index = atts.get('index', None)
        self.sex = atts['sex']
        self.role = atts['role']
        self.status = atts['status']
        self.mom = atts.get('mom_id', None)
        self.dad = atts.get('dad_id', None)
        self.layout_position = atts.get('layout', None)
        self.generated = atts.get('generated', False)

    def __repr__(self):
        return "Person({} ({}); {}; {})".format(
            self.person_id, self.family_id, self.role, self.sex)

    @property
    def dad_id(self):
        return self.dad.person_id if self.has_dad() else ''

    @property
    def mom_id(self):
        return self.mom.person_id if self.has_mom() else ''

    def has_mom(self):
        return not (self.mom is None or self.mom == '0')

    def has_dad(self):
        return not (self.dad is None or self.dad == '0')

    def has_parent(self):
        return self.has_dad() or self.has_mom()

    def has_attr(self, item):
        return item in self.atts

    def get_attr(self, item):
        return self.atts.get(item)


class Family(object):

    def _build_trios(self, persons):
        trios = {}
        for pid, p in list(persons.items()):
            if p.mom_id in persons and p.dad_id in persons:
                trios[pid] = [pid, p.mom_id, p.dad_id]
        return trios

    def _build_persons(self, ped_df):
        persons = {}
        members = []
        for index, person in enumerate(ped_df.to_dict(orient="records")):
            person['index'] = index
            person_object = Person(person)

            persons[person['person_id']] = person_object
            members.append(person_object)

        self._connect_children_with_parents(persons, members)

        return persons, members

    def _connect_children_with_parents(self, persons, members):
        for member in members:
            member.mom = persons.get(member.mom, None)
            member.dad = persons.get(member.dad, None)

    @classmethod
    def from_df(cls, family_id, ped_df):
        family = cls(family_id)
        family.ped_df = ped_df
        assert np.all(ped_df['family_id'].isin(set([family_id])).values)

        family.persons, family.members_in_order =\
            family._build_persons(family.ped_df)
        family.trios = family._build_trios(family.persons)

        return family

    def __init__(self, family_id):
        self.family_id = family_id
        self.ped_df = None
        self.members_in_order = None
        self.persons = None

    def __len__(self):
        return len(self.ped_df)

    def __repr__(self):
        return "Family({}; {})".format(self.family_id, self.members_in_order)

    def members_index(self, person_ids):
        index = []
        for pid in person_ids:
            index.append(self.persons[pid].index)
        return index

    def get_people_with_role(self, role):
        if not isinstance(role, Role):
            role = Role.from_name(role)
        return list(filter(
            lambda m: m.role == role, self.members_in_order))

    def get_people_with_roles(self, roles):
        if not isinstance(roles[0], Role):
            roles = [Role.from_name(role) for role in roles]
        return list(filter(
            lambda m: m.role in roles, self.members_in_order))

    def get_people_with_phenotype(self, phenotype_column, phenotype):
        return list(filter(
            lambda m: m.get_attr(phenotype_column) == phenotype,
            self.members_in_order))

    def get_people_with_phenotypes(self, phenotype_column, phenotypes):
        return list(filter(
            lambda m: m.get_attr(phenotype_column) in phenotypes,
            self.members_in_order))

    def get_people_with_property(self, column, value):
        return list(filter(lambda m: m.get_attr(column) == value,
                           self.members_in_order))

    def get_family_phenotypes(self, phenotype_column):
        return set([member.get_attr(phenotype_column)
                    for member in self.members_in_order])

    @property
    def members_ids(self):
        return self.ped_df['person_id'].values


class FamiliesBase(object):

    def __init__(self, ped_df=None):
        self.ped_df = ped_df
        self.families = {}
        self.family_ids = []

    def families_build(self, ped_df, family_class=Family):
        self.ped_df = ped_df
        for family_id, fam_df in self.ped_df.groupby(by='family_id'):
            family = family_class.from_df(family_id, fam_df)
            self.families[family_id] = family
            self.family_ids.append(family_id)

    def families_build_from_simple(self, fam_df, family_class=Family):
        for family_id, fam in fam_df.groupby(by='family_id'):
            family = family_class.from_df(family_id, fam_df)
            self.families[family_id] = family

    def families_query_by_person(self, person_ids):
        res = {}
        for person_id in person_ids:
            fam = self.persons[person_id]
            if fam.family_id not in res:
                res[fam.family_id] = fam
        return res

    def persons_without_parents(self):
        person = []
        for fam in list(self.families.values()):
            for p in fam.members_in_order:
                if not p.has_parent():
                    person.append(p)
        return person

    def persons_with_parents(self):
        person = []
        for fam in list(self.families.values()):
            for p in fam.members_in_order:
                if p.has_attr('with_parents'):
                    with_parents = p.get_attr('with_parents')
                    if with_parents == '1':
                        person.append(p)
                elif p.has_parent():
                    person.append(p)
        return person

    def persons_index(self, persons):
        return sorted([p.index for p in persons])

    def persons_id(self, persons):
        return sorted([p.person_id for p in persons])

    @staticmethod
    def load_simple_family_file(infile, sep="\t"):
        fam_df = pd.read_csv(
            infile, sep=sep, index_col=False,
            skipinitialspace=True,
            converters={
                'role': lambda r: Role.from_name(r),
                'gender': lambda s: Sex.from_name(s),
            },
            dtype={
                'familyId': str,
                'personId': str,
            },
            comment="#",
        )

        fam_df = fam_df.rename(columns={"gender": "sex"})

        fam_df['status'] = pd.Series(
            index=fam_df.index, data=1)
        fam_df.loc[fam_df.role == Role.prb, 'status'] = 2
        fam_df['status'] = fam_df.status.apply(lambda s: Status.from_value(s))

        fam_df['momId'] = pd.Series(
            index=fam_df.index, data='0')
        fam_df['dadId'] = pd.Series(
            index=fam_df.index, data='0')
        for fid, fam in fam_df.groupby(by='familyId'):
            mom_id = fam[fam.role == Role.mom]['personId'].iloc[0]
            dad_id = fam[fam.role == Role.dad]['personId'].iloc[0]
            children_mask = np.logical_and(
                fam_df['familyId'] == fid,
                np.logical_or(
                    fam_df.role == Role.prb,
                    fam_df.role == Role.sib))
            fam_df.loc[children_mask, 'momId'] = mom_id
            fam_df.loc[children_mask, 'dadId'] = dad_id

        if 'sampleId' not in fam_df.columns:
            sample_ids = pd.Series(data=fam_df['personId'].values)
            fam_df['sampleId'] = sample_ids

        fam_df.rename(columns={
            'personId': 'person_id',
            'familyId': 'family_id',
            'momId': 'mom_id',
            'dadId': 'dad_id',
            'sampleId': 'sample_id',
        }, inplace=True)
        return fam_df

    @staticmethod
    def load_pedigree_file(infile, sep="\t"):
        ped_df = pd.read_csv(
            infile, sep=sep, index_col=False,
            skipinitialspace=True,
            converters={
                'role': lambda r: Role.from_name(r),
                'sex': lambda s: Sex.from_name_or_value(s),
                'gender': lambda s: Sex.from_name_or_value(s),
                'status': lambda s: Status.from_name(s),
                'layout': lambda lc: lc.split(':')[-1],
                'generated': lambda g: True if g == '1.0' else False,
            },
            dtype={
                'familyId': str,
                'personId': str,
                'sampleId': str,
                'momId': str,
                'dadId': str,
            },
            comment='#',
            encoding='utf-8'
        )
        if 'gender' in ped_df.columns:
            ped_df = ped_df.rename(columns={
                'gender': 'sex',
            })

        if 'sampleId' not in ped_df.columns:
            sample_ids = pd.Series(data=ped_df['personId'].values)
            ped_df['sampleId'] = sample_ids
        else:
            sample_ids = ped_df.apply(
                lambda r: r.personId if pd.isna(r.sampleId) else r.sampleId,
                axis=1,
                result_type='reduce',
            )
            ped_df['sampleId'] = sample_ids

        ped_df.rename(columns={
            'personId': 'person_id',
            'familyId': 'family_id',
            'momId': 'mom_id',
            'dadId': 'dad_id',
            'sampleId': 'sample_id',
        }, inplace=True)
        return ped_df

    @staticmethod
    def sort_pedigree(ped_df):
        ped_df['role_order'] = ped_df['role'].apply(lambda r: r.value)
        ped_df = ped_df.sort_values(by=['familyId', 'role_order'])
        ped_df = ped_df.drop(axis=1, columns=['role_order'])
        return ped_df
