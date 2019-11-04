from collections import OrderedDict

import pandas as pd
import csv

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

    def read_file(self, file, columns_labels=None, header=None, delimiter='\t',
                  return_as_dict=False):
        if columns_labels is None:
            columns_labels = PedigreeReader.get_default_colum_labels()
        families = OrderedDict()
        with open(file) as csvfile:
            reader = csv.DictReader(csvfile, fieldnames=header,
                                    delimiter=delimiter)
            for row in reader:
                kwargs = {
                    "family_id": row[columns_labels["family_id"]],
                    "person_id": row[columns_labels["person_id"]],
                    "father": row[columns_labels["father"]],
                    "mother": row[columns_labels["mother"]],
                    "sex": row[columns_labels["sex"]],
                    "status": row[columns_labels["status"]],
                    "role": row[columns_labels["role"]],
                    "layout": row.get(columns_labels["layout"], None)
                }
                if 'generated' in columns_labels:
                    generated = row.get(columns_labels["generated"], False)
                    kwargs["generated"] = True if generated else False
                member = Person(**kwargs)
                if member.family_id not in families:
                    families[member.family_id] = Pedigree([member])
                else:
                    families[member.family_id].members.append(member)

        if return_as_dict:
            return families
        return list(families.values())

    @staticmethod
    def load_pedigree_file(pedigree_filepath, sep='\t',
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

        ped_df = pd.read_csv(
            pedigree_filepath, sep=sep, index_col=False,
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
