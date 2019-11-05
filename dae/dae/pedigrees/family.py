'''
Created on Feb 13, 2018

@author: lubo
'''
import numpy as np
import pandas as pd
from dae.variants.attributes import Role, Sex, Status


class Person(object):

    def __init__(self, **atts):
        self.atts = atts

        assert 'person_id' in atts
        self.family_id = atts['family_id']
        self.person_id = atts['person_id']
        self.sample_id = atts.get('sample_id', None)
        self.sample_index = atts.get('sampleIndex', None)
        self.index = atts.get('index', None)
        self.sex = atts['sex']
        self.role = atts['role']
        self.status = atts['status']
        self.mom_id = atts.get('mom_id', None)
        self.dad_id = atts.get('dad_id', None)
        self.mom = None
        self.dad = None
        self.layout = atts.get('layout', None)
        self.generated = atts.get('generated', False)

    def __repr__(self):
        return "Person({} ({}); {}; {})".format(
            self.person_id, self.family_id, self.role, self.sex)

    @staticmethod
    def make_person(
            person_id, family_id, mom_id, dad_id, sex, status, role,
            layout=None, generated=False):
        return Person(
            person_id=person_id,
            family_id=family_id,
            mom_id=mom_id,
            dad_id=dad_id,
            sex=sex,
            status=status,
            role=Role.from_name(role),
            layout=layout,
            generated=generated)

    @property
    def mother(self):
        return self.mom_id if self.mom_id else '0'

    @mother.setter
    def mother(self, mom_id):
        self.mom_id = mom_id

    @property
    def father(self):
        return self.dad_id if self.dad_id else '0'

    @father.setter
    def father(self, dad_id):
        self.dad_id = dad_id

    @property
    def layout_position(self):
        return self.layout

    def has_mom(self):
        return not (self.mom is None or self.mom == '0')

    def has_dad(self):
        return not (self.dad is None or self.dad == '0')

    def has_parent(self):
        return self.has_dad() or self.has_mom()

    def has_both_parents(self):
        return self.has_dad() and self.has_mom()

    def has_generated_parent(self):
        return ((self.has_dad() and self.dad.generated) or
                (self.has_mom() and self.mom.generated))

    def has_attr(self, item):
        return item in self.atts

    def get_attr(self, item):
        return str(self.atts.get(item))

    def has_missing_mother(self):
        return self.mother == '0' or self.mother == '' or self.mother is None

    def has_missing_father(self):
        return self.father == '0' or self.father == '' or self.father is None

    def has_missing_parents(self):
        return self.has_missing_father() or self.has_missing_mother()

    def get_member_dataframe(self):
        phenotype = "unknown"
        if self.status == "1":
            phenotype = "unaffected"
        elif self.status == "2":
            phenotype = "affected"
        return pd.DataFrame.from_dict({
            "family_id": [self.family_id],
            "person_id": [self.person_id],
            "sample_id": [self.person_id],
            "sex": [Sex.from_name_or_value(self.sex)],
            "role": [self.role],
            "status": [self.status],
            "mom_id": [self.mother],
            "dad_id": [self.father],
            "layout": [self.layout],
            "generated": [self.generated],
            "phenotype": [phenotype]
        })

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
            person_object = Person(**person)

            persons[person['person_id']] = person_object
            members.append(person_object)

        self._connect_children_with_parents(persons, members)

        return persons, members

    def _connect_children_with_parents(self, persons, members):
        for member in members:
            member.mom = persons.get(member.mom_id, None)
            member.dad = persons.get(member.dad_id, None)

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

    def get_people_with_people_group(
            self, people_group_column, people_group_value):
        return list(filter(
            lambda m: m.get_attr(people_group_column) == people_group_value,
            self.members_in_order))

    def get_people_with_people_groups(
            self, people_group_column, people_group_values):
        return list(filter(
            lambda m: m.get_attr(people_group_column) in people_group_values,
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

    @staticmethod
    def persons_with_parents(families):
        person = []
        for fam in list(families.values()):
            for p in fam.members_in_order:
                if p.has_attr('with_parents'):
                    with_parents = p.get_attr('with_parents')
                    if with_parents == '1':
                        person.append(p)
                elif p.has_both_parents() and (not p.has_generated_parent()):
                    person.append(p)
        return person

    @staticmethod
    def persons_ids(persons):
        return sorted([p.person_id for p in persons])


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

    def persons_index(self, persons):
        return sorted([p.index for p in persons])

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
    def sort_pedigree(ped_df):
        ped_df['role_order'] = ped_df['role'].apply(lambda r: r.value)
        ped_df = ped_df.sort_values(by=['familyId', 'role_order'])
        ped_df = ped_df.drop(axis=1, columns=['role_order'])
        return ped_df
