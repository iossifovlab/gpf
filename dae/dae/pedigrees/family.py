from functools import partial
from collections import defaultdict
from collections.abc import Mapping

import numpy as np
import pandas as pd

from dae.utils.helpers import str2bool
from dae.variants.attributes import Role, Sex, Status


class Person(object):

    def __init__(self, **attributes):
        self._attributes = attributes

        assert 'person_id' in attributes
        self.family_id = attributes['family_id']
        self.family = None
        self.person_id = attributes['person_id']
        self.sample_id = attributes.get('sample_id', None)
        self.sample_index = attributes.get('samples_index', None)
        self.index = attributes.get('index', None)

        self._sex = Sex.from_name(attributes['sex'])
        if 'role' not in attributes:
            self._role = None
        else:
            self._role = Role.from_name(attributes.get('role'))
        
        self._status = Status.from_name(attributes['status'])

        self._attributes['sex'] = self._sex
        self._attributes['role'] = self._role
        self._attributes['status'] = self._status

        self.mom_id = attributes.get('mom_id', None)
        if self.mom_id == '0':
            self.mom_id = None
            self._attributes['mom_id'] = None
        self.dad_id = attributes.get('dad_id', None)
        if self.dad_id == '0':
            self.dad_id = None
            self._attributes['dad_id'] = None
        self.mom = None
        self.dad = None

        self._layout = attributes.get('layout', None)
        self._generated = attributes.get('generated', False)

    def __repr__(self):
        return "Person({} ({}); {}; {})".format(
            self.person_id, self.family_id, self.role, self.sex)

    @property
    def role(self):
        return self._role

    @property
    def sex(self):
        return self._sex

    @property
    def status(self):
        return self._status

    @property
    def layout(self):
        return self._layout

    @property
    def generated(self):
        return self._generated

    def has_mom(self):
        return self.mom is not None

    def has_dad(self):
        return self.dad is not None

    def has_parent(self):
        return self.has_dad() or self.has_mom()

    def has_both_parents(self):
        return self.has_dad() and self.has_mom()

    def has_generated_parent(self):
        return ((self.has_dad() and self.dad.generated) or
                (self.has_mom() and self.mom.generated))

    def has_attr(self, item):
        return item in self._attributes

    def get_attr(self, item, default=None):
        return str(self._attributes.get(item, default))


class Family(object):

    def __init__(self, family_id):
        self.family_id = family_id
        self.persons = {}
        self._samples_index = None
        self._members_in_order = None
        self._trios = None

    def _connect_family(self):
        for index, member in enumerate(self.persons.values()):
            member.family = self
            member.index = index
            member.mom = self.get_member(member.mom_id, None)
            member.dad = self.get_member(member.dad_id, None)

    @staticmethod
    def from_persons(persons):
        assert len(persons) > 0
        assert all([persons[0].family_id == p.family_id for p in persons])
        family_id = persons[0].family_id

        family = Family(family_id)
        for person in persons:
            family.persons[person.person_id] = person
        family._connect_family()
        assert all([p.family is not None for p in family.persons.values()])

        return family

    def __len__(self):
        return len(self.members_in_order)

    def __repr__(self):
        return f'Family({self.family_id}, {self.members_in_order})'

    def add_members(self, persons):
        assert all([isinstance(p, Person) for p in persons])
        assert all([p.family_id == self.family_id for p in persons])

        for p in persons:
            self.persons[p.person_id] = p
        self._connect_family()
        self.redefine()

    def redefine(self):
        self._members_in_order = None
        self._trios = None
        self._samples_index = None

    @property
    def full_members(self):
        return list(self.persons.values())

    @property
    def members_in_order(self):
        if self._members_in_order is None:
            self._members_in_order = list(
                filter(lambda m: not m.generated, self.persons.values()))
        return self._members_in_order

    @property
    def members_ids(self):
        return [m.person_id for m in self.members_in_order]

    @property
    def trios(self):
        if self._trios is None:
            self._trios = {}
            members = {m.person_id: m for m in self.members_in_order}
            for pid, p in list(members.items()):
                if p.mom_id in members and p.dad_id in members:
                    self._trios[pid] = [pid, p.mom_id, p.dad_id]
        return self._trios

    @property
    def samples_index(self):
        if self._samples_index is None:
            self._samples_index = np.array([
                m.sample_index for m in self.members_in_order])
        return self._samples_index

    def members_index(self, person_ids):
        index = []
        for pid in person_ids:
            index.append(self.persons[pid].index)
        return index

    def get_member(self, person_id, default=None):
        return self.persons.get(person_id, default)

    def get_members_with_roles(self, roles):
        if not isinstance(roles[0], Role):
            roles = [Role.from_name(role) for role in roles]
        return list(filter(
            lambda m: m.role in roles, self.members_in_order))

    def get_members_with_statuses(self, statuses):
        if not isinstance(statuses[0], Status):
            statuses = [Status.from_name(status) for status in statuses]
        return list(filter(
            lambda m: m.status in statuses, self.members_in_order))


class FamiliesData(Mapping):

    def __init__(self):
        self.ped_df = None
        self._families = {}
        self.persons = {}

    @staticmethod
    def from_family_persons(family_persons):
        families_data = FamiliesData()
        for family_id, persons in family_persons:
            family = Family.from_persons(persons)
            families_data._families[family_id] = family
            for person_id, person in family.persons.items():
                families_data.persons[person_id] = person
        return families_data

    @staticmethod
    def from_pedigree_df(ped_df):
        persons = defaultdict(list)
        for rec in ped_df.to_dict(orient='record'):
            person = Person(**rec)
            persons[person.family_id].append(person)

        fams = FamiliesData.from_family_persons(
            [
                (family_id, family_persons)
                for family_id, family_persons in persons.items()
            ]
        )
        fams.ped_df = ped_df
        return fams

    @staticmethod
    def from_families(families):
        return FamiliesData.from_family_persons(
            [
                (fam.family_id, fam.full_members) for fam in families.values()
            ]
        )

    def __getitem__(self, family_id):
        return self._families[family_id]

    def __len__(self):
        return len(self._families)

    def __iter__(self):
        return iter(self._families)

    def __contains__(self, family_id):
        return family_id in self._families

    def keys(self):
        return self._families.keys()

    def values(self):
        return self._families.values()

    def items(self):
        return self._families.items()

    def get(self, family_id, default=None):
        return self._families.get(family_id, default)

    def families_query_by_person_ids(self, person_ids):
        res = {}
        for person_id in person_ids:
            person = self.persons[person_id]
            if person.family_id in res:
                continue
            family = self._families[person.family_id]
            res[family.family_id] = family
        return res

    def persons_without_parents(self):
        person = []
        for fam in list(self._families.values()):
            for p in fam.members_in_order:
                if not p.has_parent():
                    person.append(p)
        return person

    def persons_with_parents(self):
        person = []
        for fam in list(self._families.values()):
            for p in fam.members_in_order:
                if p.has_both_parents() and (not p.has_generated_parent()):
                    person.append(p)
        return person

    def persons_with_roles(self, roles):
        if not isinstance(roles[0], Role):
            roles = [Role.from_name(role) for role in roles]
        return list(filter(
            lambda m: m.role in roles, self.persons.values()))


PEDIGREE_COLUMN_NAMES = {
    'family': 'family_id',
    'person': 'person_id',
    'mother': 'mom_id',
    'father': 'dad_id',
    'sex': 'sex',
    'status': 'status',
    'role': 'role',
    'sample id': 'sample_id',
    'layout': 'layout',
    'generated': 'generated',
}


PED_COLUMNS_REQUIRED = (
    PEDIGREE_COLUMN_NAMES['family'],
    PEDIGREE_COLUMN_NAMES['person'],
    PEDIGREE_COLUMN_NAMES['mother'],
    PEDIGREE_COLUMN_NAMES['father'],
    PEDIGREE_COLUMN_NAMES['sex'],
    PEDIGREE_COLUMN_NAMES['status'],
)


class FamiliesLoader:

    def __init__(self, families_filename, params={}, sep='\t'):

        self.families_filename = families_filename
        self.params = params
        self.params['sep'] = sep
        self.file_format = params.get('ped_file_format', 'pedigree')

    @staticmethod
    def load_pedigree_file(pedigree_filename, pedigree_format={}):
        ped_df = FamiliesLoader.flexible_pedigree_read(
            pedigree_filename, **pedigree_format
        )
        families = FamiliesData.from_pedigree_df(ped_df)
        if pedigree_format.get('ped_no_role'):
            for family in families.values():
                role_build = FamilyRoleBuilder(family)
                role_build.build_roles()

        return families

    @staticmethod
    def load_simple_families_file(families_filename):
        ped_df = FamiliesLoader.load_simple_family_file(
            families_filename
        )
        return FamiliesData.from_pedigree_df(ped_df)

    def load(self):
        if self.file_format == 'simple':
            return self.load_simple_families_file(self.families_filename)
        else:
            assert self.file_format == 'pedigree'
            return self.load_pedigree_file(
                self.families_filename, pedigree_format=self.params)

    @staticmethod
    def cli_arguments(parser):
        parser.add_argument(
            '--ped-family',
            default='familyId',
            help='specify the name of the column in the pedigree file that '
            'holds '
            'the ID of the family the person belongs to [default: %(default)s]'
        )

        parser.add_argument(
            '--ped-person',
            default='personId',
            help='specify the name of the column in the pedigree file that '
            'holds '
            'the person\'s ID [default: %(default)s]'
        )

        parser.add_argument(
            '--ped-mom',
            default='momId',
            help='specify the name of the column in the pedigree file that '
            'holds '
            'the ID of the person\'s mother [default: %(default)s]'
        )

        parser.add_argument(
            '--ped-dad',
            default='dadId',
            help='specify the name of the column in the pedigree file that '
            'holds '
            'the ID of the person\'s father [default: %(default)s]'
        )

        parser.add_argument(
            '--ped-sex',
            default='sex',
            help='specify the name of the column in the pedigree file that '
            'holds '
            'the sex of the person [default: %(default)s]'
        )

        parser.add_argument(
            '--ped-status',
            default='status',
            help='specify the name of the column in the pedigree file that '
            'holds '
            'the status of the person [default: %(default)s]'
        )

        parser.add_argument(
            '--ped-role',
            default='role',
            help='specify the name of the column in the pedigree file that '
            'holds '
            'the role of the person [default: %(default)s]'
        )

        parser.add_argument(
            '--ped-no-role',
            action='store_true',
            help='indicates that the provided pedigree file has no role '
            'column. '
            'If this argument is provided, the import tool will guess the '
            'roles '
            'of individuals and write them in a "role" column.'
        )

        parser.add_argument(
            '--ped-no-header',
            action='store_true',
            help='indicates that the provided pedigree file has no header. '
            'The '
            'pedigree column arguments will accept indices if this argument '
            'is '
            'given. [default: %(default)s]'
        )

        parser.add_argument(
            '--ped-file-format',
            default='pedigree',
            help='Families file format. It should `pedigree` or `simple`'
            'for simple family format [default: %(default)s]'
        )

    @classmethod
    def parse_cli_arguments(cls, argv):
        ped_ped_args = [
            'ped_family',
            'ped_person',
            'ped_mom',
            'ped_dad',
            'ped_sex',
            'ped_status',
            'ped_role',
            'ped_no_role',
            'ped_file_format',
        ]
        ped_has_header = not argv.ped_no_header
        res = {}
        res['ped_has_header'] = ped_has_header

        for col in ped_ped_args:
            ped_value = getattr(argv, col)
            if ped_has_header:
                res[col] = ped_value
            else:
                assert ped_value.isnumeric(), \
                    '{} must hold an integer value!'.format(col)
                res[col] = int(ped_value)

        return res

    @staticmethod
    def produce_header_from_indices(
       ped_family,
       ped_person,
       ped_mom,
       ped_dad,
       ped_sex,
       ped_status,
       ped_role,
       ped_layout,
       ped_generated,
       ped_sample_id,
    ):
        header = (
            (ped_family, PEDIGREE_COLUMN_NAMES['family']),
            (ped_person, PEDIGREE_COLUMN_NAMES['person']),
            (ped_mom, PEDIGREE_COLUMN_NAMES['mother']),
            (ped_dad, PEDIGREE_COLUMN_NAMES['father']),
            (ped_sex, PEDIGREE_COLUMN_NAMES['sex']),
            (ped_status, PEDIGREE_COLUMN_NAMES['status']),
            (ped_role, PEDIGREE_COLUMN_NAMES['role']),
            (ped_layout, PEDIGREE_COLUMN_NAMES['layout']),
            (ped_generated, PEDIGREE_COLUMN_NAMES['generated']),
            (ped_sample_id, PEDIGREE_COLUMN_NAMES['sample id']),
        )
        header = tuple(filter(lambda col: type(col[0]) is int, header))
        for col in header:
            assert type(col[0]) is int, col[0]
        header = tuple(sorted(header, key=lambda col: col[0]))
        return zip(*header)

    @staticmethod
    def flexible_pedigree_read(
            pedigree_filepath, sep='\t',
            ped_has_header=True,
            ped_family='familyId',
            ped_person='personId',
            ped_mom='momId',
            ped_dad='dadId',
            ped_sex='sex',
            ped_status='status',
            ped_role='role',
            ped_layout='layout',
            ped_generated='generated',
            ped_sample_id='sampleId',
            ped_no_role=False,
            **kwargs):

        if type(ped_no_role) == str:
            ped_no_role = str2bool(ped_no_role)
        if type(ped_has_header) == str:
            ped_has_header = str2bool(ped_has_header)

        read_csv_func = partial(
            pd.read_csv,
            sep=sep,
            index_col=False,
            skipinitialspace=True,
            converters={
                ped_role: Role.from_name,
                ped_sex: Sex.from_name_or_value,
                ped_status: Status.from_name_or_value,
                ped_layout: lambda lc: lc.split(':')[-1],
                ped_generated: lambda g: True if g == '1.0' else False,
            },
            dtype=str,
            comment='#',
            encoding='utf-8'
        )

        if not ped_has_header:
            _, file_header = FamiliesLoader.produce_header_from_indices(
                ped_family, ped_person, ped_mom,
                ped_dad, ped_sex, ped_status,
                ped_role, ped_layout, ped_generated, ped_sample_id,
            )
            ped_family = PEDIGREE_COLUMN_NAMES['family']
            ped_person = PEDIGREE_COLUMN_NAMES['person']
            ped_mom = PEDIGREE_COLUMN_NAMES['mother']
            ped_dad = PEDIGREE_COLUMN_NAMES['father']
            ped_sex = PEDIGREE_COLUMN_NAMES['sex']
            ped_status = PEDIGREE_COLUMN_NAMES['status']
            ped_role = PEDIGREE_COLUMN_NAMES['role']
            ped_layout = PEDIGREE_COLUMN_NAMES['layout']
            ped_generated = PEDIGREE_COLUMN_NAMES['generated']
            ped_sample_id = PEDIGREE_COLUMN_NAMES['sample id']
            ped_df = read_csv_func(
                pedigree_filepath, header=None, names=file_header
            )
        else:
            ped_df = read_csv_func(pedigree_filepath)

        if ped_sample_id in ped_df:
            sample_ids = ped_df.apply(
                lambda r: r.personId if pd.isna(r.sampleId) else r.sampleId,
                axis=1,
                result_type='reduce',
            )
            ped_df[ped_sample_id] = sample_ids
        else:
            sample_ids = pd.Series(data=ped_df[ped_person].values)
            ped_df[ped_sample_id] = sample_ids

        ped_df = ped_df.rename(columns={
            ped_family: PEDIGREE_COLUMN_NAMES['family'],
            ped_person: PEDIGREE_COLUMN_NAMES['person'],
            ped_mom: PEDIGREE_COLUMN_NAMES['mother'],
            ped_dad: PEDIGREE_COLUMN_NAMES['father'],
            ped_sex: PEDIGREE_COLUMN_NAMES['sex'],
            ped_status: PEDIGREE_COLUMN_NAMES['status'],
            ped_role: PEDIGREE_COLUMN_NAMES['role'],
            ped_sample_id: PEDIGREE_COLUMN_NAMES['sample id'],
        })

        assert set(PED_COLUMNS_REQUIRED) <= set(ped_df.columns), \
            ped_df.columns

        # if ped_no_role:
        #     ped_df = PedigreeRoleGuesser.guess_role_nuc(ped_df)

        return ped_df

    @staticmethod
    def load_simple_family_file(infile, sep="\t"):
        fam_df = pd.read_csv(
            infile, sep=sep, index_col=False,
            skipinitialspace=True,
            converters={
                'role': lambda r: Role.from_name(r),
                'gender': lambda s: Sex.from_name(s),
                'sex': lambda s: Sex.from_name(s),
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
    def save_pedigree(ped_df, filename):
        df = ped_df.copy()

        df = df.rename(columns={
            'person_id': 'personId',
            'family_id': 'familyId',
            'mom_id': 'momId',
            'dad_id': 'dadId',
            'sample_id': 'sampleId',
        })
        df.sex = df.sex.apply(lambda v: v.name)
        df.role = df.role.apply(lambda v: v.name)
        df.status = df.status.apply(lambda v: v.name)

        df.to_csv(filename, index=False, sep='\t')

    @staticmethod
    def get_default_colum_labels():
        return {
            "family_id": "familyId",
            "person_id": "personId",
            "father": "dadId",
            "mother": "momId",
            "sex": "sex",
            "status": "status",
            "role": "role",
            "layout": "layout"
        }

    @staticmethod
    def sort_pedigree(ped_df):
        ped_df['role_order'] = ped_df['role'].apply(lambda r: r.value)
        ped_df = ped_df.sort_values(by=['familyId', 'role_order'])
        ped_df = ped_df.drop(axis=1, columns=['role_order'])
        return ped_df


class Mating:

    def __init__(self, mom_id, dad_id):
        self.mom_id = mom_id
        self.dad_id = dad_id
        self.id = Mating.build_id(mom_id, dad_id)
        self.children = set()

    @staticmethod
    def build_id(mom_id, dad_id):
        return f'{mom_id},{dad_id}'

    @staticmethod
    def parents_id(person):
        return Mating.build_id(person.mom_id, person.dad_id)


class FamilyRoleBuilder:

    def __init__(self, family):
        self.family = family
        self.family_matings = self._build_family_matings()
        self.members_matings = self._build_members_matings()

    def build_roles(self):
        proband = self._get_family_proband()
        assert proband is not None
        self._set_person_role(proband, Role.prb)

        self._assign_roles_children(proband)
        self._assign_roles_mates(proband)
        self._assign_roles_parents(proband)
        self._assign_roles_siblings(proband)
        self._assign_roles_paternal(proband)
        self._assign_roles_maternal(proband)

    @classmethod
    def _set_person_role(cls, person, role):
        assert isinstance(person, Person)
        assert isinstance(role, Role)
        person._role = role
        person._attributes['role'] = role

    def _get_family_proband(self):
        probands = self.family.get_members_with_roles([Role.prb])
        if len(probands) > 0:
            return probands[0]
        affected = self.family.get_members_with_statuses([Status.affected])
        if len(affected) > 0:
            return affected[0]
        return None

    def _build_family_matings(self):
        matings = {}

        for person_id, person in self.family.persons.items():
            if person.has_parent():

                parents_mating_id = Mating.parents_id(person)
                if parents_mating_id not in matings:
                    parents = Mating(person.mom_id, person.dad_id)
                    matings[parents_mating_id] = parents
                parents_mating = matings.get(parents_mating_id)
                assert parents_mating is not None
                parents_mating.children.add(person_id)
        return matings

    def _build_members_matings(self):
        members_matings = defaultdict(set)
        for mating_id, mating in self.family_matings.items():
            if mating.mom_id is not None:
                members_matings[mating.mom_id].add(mating_id)
            if mating.dad_id is not None:
                members_matings[mating.dad_id].add(mating_id)
        return members_matings

    def _assign_roles_children(self, proband):
        for mating_id in self.members_matings[proband.person_id]:
            mating = self.family_matings[mating_id]
            for child_id in mating.children:
                child = self.family.persons[child_id]
                self._set_person_role(child, Role.child)

    def _assign_roles_mates(self, proband):
        for mating_id in self.members_matings[proband.person_id]:
            mating = self.family_matings[mating_id]
            if mating.dad_id is not None \
                    and mating.dad_id != proband.person_id:
                person = self.family.persons[mating.dad_id]
                self._set_person_role(person, Role.spouse)
            elif mating.mom_id is not None \
                    and mating.mom_id != proband.person_id:
                person = self.family.persons[mating.mom_id]
                self._set_person_role(person, Role.spouse)

    def _assign_roles_parents(self, proband):
        if not proband.has_parent():
            return
        if proband.mom is not None:
            self._set_person_role(proband.mom, Role.mom)
        if proband.dad is not None:
            self._set_person_role(proband.dad, Role.dad)

    def _assign_roles_siblings(self, proband):
        if not proband.has_parent():
            return
        parents_mating = self.family_matings[Mating.parents_id(proband)]
        for person_id in parents_mating.children:
            if person_id != proband.person_id:
                person = self.family.persons[person_id]
                self._set_person_role(person, Role.sib)

    def _assign_roles_paternal(self, proband):
        if proband.dad is None or not proband.dad.has_parent():
            return

        dad = proband.dad
        if dad.dad is not None:
            self._set_person_role(dad.dad, Role.paternal_grandfather)
        if dad.mom is not None:
            self._set_person_role(dad.mom, Role.paternal_grandmother)

        grandparents_mating_id = Mating.parents_id(dad)
        grandparents_mating = self.family_matings[grandparents_mating_id]
        for person_id in grandparents_mating.children:    
            person = self.family.persons[person_id]
            if person.role is not None:
                continue
            if person.sex == Sex.M:
                self._set_person_role(person, Role.paternal_uncle)
            if person.sex == Sex.F:
                self._set_person_role(person, Role.paternal_aunt)

            for person_mating_id in self.members_matings[person.person_id]:
                person_mating = self.family_matings[person_mating_id]
                for cousin_id in person_mating.children:
                    cousin = self.family.persons[cousin_id]
                    self._set_person_role(cousin, Role.paternal_cousin)

    def _assign_roles_maternal(self, proband):
        if proband.mom is None or not proband.mom.has_parent():
            return

        mom = proband.mom
        if mom.dad is not None:
            self._set_person_role(mom.dad, Role.maternal_grandfather)
        if mom.mom is not None:
            self._set_person_role(mom.mom, Role.maternal_grandmother)

        grandparents_mating_id = Mating.parents_id(mom)
        grandparents_mating = self.family_matings[grandparents_mating_id]
        for person_id in grandparents_mating.children:    
            person = self.family.persons[person_id]
            if person.role is not None:
                continue
            if person.sex == Sex.M:
                self._set_person_role(person, Role.maternal_uncle)
            if person.sex == Sex.F:
                self._set_person_role(person, Role.maternal_aunt)

            for person_mating_id in self.members_matings[person.person_id]:
                person_mating = self.family_matings[person_mating_id]
                for cousin_id in person_mating.children:
                    cousin = self.family.persons[cousin_id]
                    self._set_person_role(cousin, Role.maternal_cousin)


# class PedigreeRoleGuesser():

#     @staticmethod
#     def _find_parent_in_family_ped(family_df, mom_or_dad):
#         df = family_df[family_df[mom_or_dad] != '0']
#         assert len(df[mom_or_dad].unique()) <= 1
#         if len(df) > 0:
#             row = df.iloc[0]
#             return (row.family_id, row[mom_or_dad])
#         return None

#     @staticmethod
#     def _find_mom_in_family_ped(family_df):
#         return PedigreeRoleGuesser._find_parent_in_family_ped(
#             family_df, 'mom_id')

#     @staticmethod
#     def _find_dad_in_family_ped(family_df):
#         return PedigreeRoleGuesser._find_parent_in_family_ped(
#             family_df, 'dad_id')

#     @staticmethod
#     def _find_status_in_family(family_df, status):
#         df = family_df[family_df.status == status]
#         result = []
#         for row in df.to_dict('records'):
#             result.append((row['family_id'], row['person_id']))
#         return result

#     @staticmethod
#     def _find_prb_in_family(family_df):
#         return PedigreeRoleGuesser._find_status_in_family(
#             family_df, Status.affected)

#     @staticmethod
#     def _find_sib_in_family(family_df):
#         return PedigreeRoleGuesser._find_status_in_family(
#             family_df, Status.unaffected)

#     @staticmethod
#     def guess_role_nuc(ped_df):
#         res_df = ped_df.copy()

#         grouped = res_df.groupby('family_id')
#         roles = {}
#         for _, family_df in grouped:
#             mom = PedigreeRoleGuesser._find_mom_in_family_ped(family_df)
#             if mom:
#                 roles[mom] = Role.mom
#             dad = PedigreeRoleGuesser._find_dad_in_family_ped(family_df)
#             if dad:
#                 roles[dad] = Role.dad
#             for p in PedigreeRoleGuesser._find_prb_in_family(family_df):
#                 if p not in roles:
#                     roles[p] = Role.prb
#             for p in PedigreeRoleGuesser._find_sib_in_family(family_df):
#                 if p not in roles:
#                     roles[p] = Role.sib
#         assert len(roles) == len(res_df)

#         role = pd.Series(res_df.index)
#         for index, row in res_df.iterrows():
#             role[index] = roles[(row['family_id'], row['person_id'])]
#         res_df['role'] = role
#         return res_df
