from functools import partial

import numpy as np
import pandas as pd

from dae.variants.attributes import Role, Sex, Status
from dae.pedigrees.pedigrees import Pedigree
from dae.pedigrees.family import Person


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


class PedigreeReader(object):

    @staticmethod
    def read_file(
            pedigree_filepath, sep='\t',
            col_family='familyId', col_person='personId', col_mom='momId',
            col_dad='dadId', col_sex='sex', col_status='status',
            col_role='role',
            col_layout='layout', col_generated='generated',
            col_sample_id='sampleId',
            return_as_dict=False):

        ped_df = PedigreeReader.flexible_pedigree_read(
            pedigree_filepath, sep=sep,
            col_family=col_family, col_person=col_person,
            col_mom=col_mom, col_dad=col_dad,
            col_sex=col_sex, col_status=col_status,
            col_role=col_role, col_layout=col_layout,
            col_generated=col_generated, col_sample_id=col_sample_id)

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
       col_family,
       col_person,
       col_mom,
       col_dad,
       col_sex,
       col_status,
       col_role,
       col_layout,
       col_generated,
       col_sample_id,
    ):
        header = (
            (col_family, PEDIGREE_COLUMN_NAMES['family']),
            (col_person, PEDIGREE_COLUMN_NAMES['person']),
            (col_mom, PEDIGREE_COLUMN_NAMES['mother']),
            (col_dad, PEDIGREE_COLUMN_NAMES['father']),
            (col_sex, PEDIGREE_COLUMN_NAMES['sex']),
            (col_status, PEDIGREE_COLUMN_NAMES['status']),
            (col_role, PEDIGREE_COLUMN_NAMES['role']),
            (col_layout, PEDIGREE_COLUMN_NAMES['layout']),
            (col_generated, PEDIGREE_COLUMN_NAMES['generated']),
            (col_sample_id, PEDIGREE_COLUMN_NAMES['sample id']),
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

    @staticmethod
    def flexible_pedigree_read(
            pedigree_filepath, sep='\t',
            has_header=True,
            col_family='familyId',
            col_person='personId',
            col_mom='momId',
            col_dad='dadId',
            col_sex='sex',
            col_status='status',
            col_role='role',
            col_layout='layout',
            col_generated='generated',
            col_sample_id='sampleId'):

        read_csv_func = partial(
            pd.read_csv,
            sep=sep,
            index_col=False,
            skipinitialspace=True,
            converters={
                col_role: Role.from_name,
                col_sex: Sex.from_name_or_value,
                col_status: Status.from_name_or_value,
                col_layout: lambda lc: lc.split(':')[-1],
                col_generated: lambda g: True if g == '1.0' else False,
            },
            dtype={
                col_family: str,
                col_person: str,
                col_mom: str,
                col_dad: str,
                col_sample_id: str,
            },
            comment='#',
            encoding='utf-8'
        )

        if not has_header:
            _, file_header = PedigreeReader.produce_header_from_indices(
                col_family, col_person, col_mom,
                col_dad, col_sex, col_status,
                col_role, col_layout, col_generated, col_sample_id,
            )
            col_family = PEDIGREE_COLUMN_NAMES['family']
            col_person = PEDIGREE_COLUMN_NAMES['person']
            col_mom = PEDIGREE_COLUMN_NAMES['mother']
            col_dad = PEDIGREE_COLUMN_NAMES['father']
            col_sex = PEDIGREE_COLUMN_NAMES['sex']
            col_status = PEDIGREE_COLUMN_NAMES['status']
            col_role = PEDIGREE_COLUMN_NAMES['role']
            col_layout = PEDIGREE_COLUMN_NAMES['layout']
            col_generated = PEDIGREE_COLUMN_NAMES['generated']
            col_sample_id = PEDIGREE_COLUMN_NAMES['sample id']
            ped_df = read_csv_func(
                pedigree_filepath, header=None, names=file_header
            )
        else:
            ped_df = read_csv_func(pedigree_filepath)

        if col_sample_id in ped_df:
            sample_ids = ped_df.apply(
                lambda r: r.personId if pd.isna(r.sampleId) else r.sampleId,
                axis=1,
                result_type='reduce',
            )
            ped_df[col_sample_id] = sample_ids
        else:
            sample_ids = pd.Series(data=ped_df[col_person].values)
            ped_df[col_sample_id] = sample_ids

        ped_df = ped_df.rename(columns={
            col_family: PEDIGREE_COLUMN_NAMES['family'],
            col_person: PEDIGREE_COLUMN_NAMES['person'],
            col_mom: PEDIGREE_COLUMN_NAMES['mother'],
            col_dad: PEDIGREE_COLUMN_NAMES['father'],
            col_sex: PEDIGREE_COLUMN_NAMES['sex'],
            col_status: PEDIGREE_COLUMN_NAMES['status'],
            col_role: PEDIGREE_COLUMN_NAMES['role'],
            col_sample_id: PEDIGREE_COLUMN_NAMES['sample id'],
        })

        assert set(PED_COLUMNS_REQUIRED) <= set(ped_df.columns), \
            ped_df.columns

        return ped_df

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
