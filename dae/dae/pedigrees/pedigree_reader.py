from collections import OrderedDict

import pandas as pd
import csv

from dae.variants.attributes import Role, Sex, Status
from dae.pedigrees.pedigrees import Pedigree, PedigreeMember


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
    PEDIGREE_COLUMN_NAMES['role'],
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
                    "id": row[columns_labels["id"]],
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
                member = PedigreeMember(**kwargs)
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

        if col_sex not in ped_df:
            if 'gender' in ped_df:
                ped_df['gender'] = \
                    list(map(Sex.from_name_or_value, ped_df['gender']))
                ped_df = ped_df.rename(columns={
                    'gender': PEDIGREE_COLUMN_NAMES['sex']
                })

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
            col_sample_id: PEDIGREE_COLUMN_NAMES['sample id'],
        })

        assert set(PED_COLUMNS_REQUIRED) <= set(ped_df.columns)

        return ped_df

    @staticmethod
    def get_default_colum_labels():
        return {
            "family_id": "familyId",
            "id": "personId",
            "father": "dadId",
            "mother": "momId",
            "sex": "gender",
            "status": "status",
            "role": "role",
            "layout": "layout"
        }
