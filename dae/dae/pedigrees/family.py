import os

from functools import partial

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
        self.sample_index = atts.get('samples_index', None)
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

    def _build_persons(self, ped_df):
        persons = {}
        for index, rec in enumerate(ped_df.to_dict(orient="records")):
            rec['index'] = index
            person = Person(**rec)
            person_id = person.person_id
            persons[person_id] = person

        self._connect_children_with_parents(persons)
        return persons

    def _connect_children_with_parents(self, persons):
        for member in persons.values():
            member.mom = persons.get(member.mom_id, None)
            member.dad = persons.get(member.dad_id, None)

    @staticmethod
    def from_df(family_id, ped_df):
        family = Family(family_id)
        assert np.all(ped_df['family_id'].isin(set([family_id])).values)

        family.persons =\
            family._build_persons(ped_df)
        assert family._members_in_order is None

        return family

    def __init__(self, family_id):
        self.family_id = family_id
        self.persons = None
        self._samples_index = None
        self._members_in_order = None
        self._trios = None

    def __len__(self):
        return len(self.members_in_order)

    # def __repr__(self):
    #     return "Family({}; {})".format(self.family_id, self.members_in_order)

    def redefine(self):
        self._members_in_order = None
        self._trios = None
        self._samples_index = None

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


class FamiliesData(object):

    def __init__(self, ped_df=None):
        # assert ped_df is not None
        self.ped_df = ped_df
        self.families = {}
        self.persons = {}
        self.family_ids = []
        # self._families_build(ped_df, family_class)

    def _families_build(self, ped_df):
        self.ped_df = ped_df
        for family_id, fam_df in self.ped_df.groupby(by='family_id'):
            family = Family.from_df(family_id, fam_df)
            self.families[family_id] = family
            self.family_ids.append(family_id)
            for person_id, person in family.persons.items():
                self.persons[person_id] = person

    @staticmethod
    def from_pedigree_df(ped_df):
        fams = FamiliesData(ped_df)
        fams._families_build(ped_df)
        return fams

    def families_list(self):
        return list(self.families.values())

    def get_family(self, family_id):
        return self.families[family_id]

    def has_family(self, family_id):
        return family_id in self.families

    def families_query_by_person(self, person_ids):
        res = {}
        for person_id in person_ids:
            people = self.ped_df.loc[self.ped_df['person_id'] == person_id]
            assert len(people) == 1
            famId = people.loc[:, 'family_id'].iloc[0]
            fam = self.families[famId]
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


class Pedigree(object):

    def __init__(self, members):
        self._members = members
        self.family_id = members[0].family_id if len(members) > 0 else ""
        self._independent_members = None

    @property
    def members(self):
        return self._members

    def add_members(self, new_members):
        self._members += new_members

    def add_member(self, member):
        self._members.append(member)
        self._independent_members = None

    def independent_members(self):
        if not self._independent_members:
            self._independent_members = \
                [m for m in self._members if m.has_missing_parents()]

        return self._independent_members

    def get_pedigree_dataframe(self):
        return pd.concat([member.get_member_dataframe()
                          for member in self._members])


class FamiliesLoader:

    def __init__(self, families_filename, params={}):

        assert os.path.exists(families_filename)
        self.families_filename = families_filename
        self.pedigree_format = params
        self.file_format = params.get('ped_file_format', 'pedigree')

        self.families = self._load_families_data()
        self.ped_df = self.families.ped_df

    @staticmethod
    def load_pedigree_file(pedigree_filename, pedigree_format={}):
        ped_df = PedigreeReader.flexible_pedigree_read(
            pedigree_filename, **pedigree_format
        )
        return FamiliesData.from_pedigree_df(ped_df)

    @staticmethod
    def load_simple_families_file(families_filename):
        ped_df = PedigreeReader.load_simple_family_file(
            families_filename
        )
        return FamiliesData.from_pedigree_df(ped_df)

    def _load_families_data(self):
        if self.file_format == 'simple':
            assert not self.pedigree_format
            return self.load_simple_families_file(self.families_filename)
        else:
            assert self.file_format == 'pedigree'
            return self.load_pedigree_file(
                self.families_filename, pedigree_format=self.pedigree_format)


class PedigreeReader(object):

    @staticmethod
    def read_file(
            pedigree_filepath, sep='\t',
            ped_family='familyId', ped_person='personId', ped_mom='momId',
            ped_dad='dadId', ped_sex='sex', ped_status='status',
            ped_role='role',
            ped_layout='layout', ped_generated='generated',
            ped_sample_id='sampleId',
            return_as_dict=False):

        ped_df = PedigreeReader.flexible_pedigree_read(
            pedigree_filepath, sep=sep,
            ped_family=ped_family, ped_person=ped_person,
            ped_mom=ped_mom, ped_dad=ped_dad,
            ped_sex=ped_sex, ped_status=ped_status,
            ped_role=ped_role, ped_layout=ped_layout,
            ped_generated=ped_generated, ped_sample_id=ped_sample_id)

        families = {}
        for row in ped_df.to_dict(orient='records'):
            kwargs = {
                "family_id": row["family_id"],
                "person_id": row["person_id"],
                "father": row["dad_id"],
                "mother": row["mom_id"],
                "sex": row["sex"],
                "status": row["status"],
                "role": row["role"],
                "layout": row.get("layout", None),
                "generated": row.get("generated", False),
            }
            member = Person(**kwargs)
            if member.family_id not in families:
                families[member.family_id] = Pedigree([member])
            else:
                families[member.family_id].members.append(member)

        if return_as_dict:
            return families
        return list(families.values())

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
    def flexible_pedigree_cli_arguments(parser):
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
    def flexible_pedigree_parse_cli_arguments(cls, argv):
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
        has_header = not argv.ped_no_header
        res = {}
        res['has_header'] = has_header

        for col in ped_ped_args:
            ped_value = getattr(argv, col)
            if has_header:
                res[col] = ped_value
            else:
                assert ped_value.isnumeric(), \
                    '{} must hold an integer value!'.format(col)
                res[col] = int(ped_value)

        return res

    @staticmethod
    def flexible_pedigree_read(
            pedigree_filepath, sep='\t',
            has_header=True,
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
            dtype={
                ped_family: str,
                ped_person: str,
                ped_mom: str,
                ped_dad: str,
                ped_sample_id: str,
            },
            comment='#',
            encoding='utf-8'
        )

        if not has_header:
            _, file_header = PedigreeReader.produce_header_from_indices(
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

        if ped_no_role:
            ped_df = PedigreeRoleGuesser.guess_role_nuc(ped_df)

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


class PedigreeRoleGuesser():

    @staticmethod
    def _find_parent_in_family_ped(family_df, mom_or_dad):
        df = family_df[family_df[mom_or_dad] != '0']
        assert len(df[mom_or_dad].unique()) <= 1
        if len(df) > 0:
            row = df.iloc[0]
            return (row.family_id, row[mom_or_dad])
        return None

    @staticmethod
    def _find_mom_in_family_ped(family_df):
        return PedigreeRoleGuesser._find_parent_in_family_ped(
            family_df, 'mom_id')

    @staticmethod
    def _find_dad_in_family_ped(family_df):
        return PedigreeRoleGuesser._find_parent_in_family_ped(
            family_df, 'dad_id')

    @staticmethod
    def _find_status_in_family(family_df, status):
        df = family_df[family_df.status == status]
        result = []
        for row in df.to_dict('records'):
            result.append((row['family_id'], row['person_id']))
        return result

    @staticmethod
    def _find_prb_in_family(family_df):
        return PedigreeRoleGuesser._find_status_in_family(
            family_df, Status.affected)

    @staticmethod
    def _find_sib_in_family(family_df):
        return PedigreeRoleGuesser._find_status_in_family(
            family_df, Status.unaffected)

    @staticmethod
    def guess_role_nuc(ped_df):
        res_df = ped_df.copy()

        grouped = res_df.groupby('family_id')
        roles = {}
        for _, family_df in grouped:
            mom = PedigreeRoleGuesser._find_mom_in_family_ped(family_df)
            if mom:
                roles[mom] = Role.mom
            dad = PedigreeRoleGuesser._find_dad_in_family_ped(family_df)
            if dad:
                roles[dad] = Role.dad
            for p in PedigreeRoleGuesser._find_prb_in_family(family_df):
                if p not in roles:
                    roles[p] = Role.prb
            for p in PedigreeRoleGuesser._find_sib_in_family(family_df):
                if p not in roles:
                    roles[p] = Role.sib
        assert len(roles) == len(res_df)

        role = pd.Series(res_df.index)
        for index, row in res_df.iterrows():
            role[index] = roles[(row['family_id'], row['person_id'])]
        res_df['role'] = role
        return res_df
