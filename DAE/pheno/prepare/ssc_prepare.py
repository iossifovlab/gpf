'''
Created on Sep 18, 2017

@author: lubo
'''
import os

import pandas as pd
import numpy as np
from variants.attributes import Role, Sex, Status


def load_and_join():
    data_db_dir = os.environ['DAE_DB_DIR']
    data_dev_dir = os.environ.get('DAE_DATA_DIR', data_db_dir)

    individuals_v15_filename = os.path.join(
        data_dev_dir,
        'pheno/15',
        'Individuals_by_Distribution_v15.csv')

    individuals_v14_filename = os.path.join(
        data_dev_dir,
        'pheno/14',
        'individual.csv')

    persons_filename = os.path.join(
        data_dev_dir,
        'pheno/15',
        'persons.csv'
    )

    individuals_v14_age_of_assessment_filename = os.path.join(
        data_dev_dir,
        'pheno/14',
        'ssc_age_at_assessment.csv')
    persons_df = pd.read_csv(individuals_v15_filename, sep='\t')
    persons_df = persons_df.rename(columns={"SSC ID": "personId"})

    individuals_df = pd.read_csv(
        persons_filename, sep=',',
        dtype={
            'family_id': object,
            'person_id': object,
        }
    )
    individuals_df = individuals_df.rename(
        columns={
            'person_id': 'personId',
            'family_id': 'familyId',
            'sex': 'sexI',
            'role': 'roleI'
        })
    assert 'personId' in individuals_df.columns

    persons_14_df = pd.read_csv(individuals_v14_filename)
    persons_14_df = persons_14_df.rename(columns={"id()": "personId"})
    assert 'personId' in persons_14_df.columns

    persons_14_age_df = pd.read_csv(
        individuals_v14_age_of_assessment_filename,
        sep=',')
    persons_14_age_df = persons_14_age_df.rename(
        columns={"portalId": "personId"})
    assert 'personId' in persons_14_age_df.columns

    persons_df = persons_df[persons_df["Version 15: 2013-08-06"] == 1]

    persons_14_age_df.set_index('personId', inplace=True)
    persons_14_df.set_index('personId', inplace=True)
    individuals_df.set_index('personId', inplace=True)

    persons_df = persons_df.join(
        individuals_df, on='personId', rsuffix='_individual')
    persons_df = persons_df.join(persons_14_df, on='personId')
    persons_df = persons_df.join(persons_14_age_df, on='personId')

    measure_df = load_instrument('ssc_core_descriptive')
    measure_df = measure_df.rename(columns={'individual': 'personId'})
    measure_df.set_index('personId', inplace=True)

    persons_df = persons_df.join(measure_df, on='personId', rsuffix="_core")

    return persons_df


def load_instrument(instrument_name):
    data_db_dir = os.environ['DAE_DB_DIR']
    data_dev_dir = os.environ.get('DAE_DATA_DIR', data_db_dir)

    pheno_ssc_15_dir = os.path.join(data_dev_dir, 'pheno/15/instruments')
    ssc_measures_dirs = [
        'Designated Unaffected Sibling Data',
        'Father Data',
        'Mother Data',
        'MZ Twin Data',
        'Other Sibling Data',
        'Proband Data'
    ]

    ssc_core_descriptive_filenames = [
        os.path.join(
            pheno_ssc_15_dir,
            measure_dir,
            '{}.csv'.format(instrument_name)
        )
        for measure_dir in ssc_measures_dirs
    ]
    assert all([os.path.exists(filename)
                for filename in ssc_core_descriptive_filenames])

    measures_df = [
        pd.read_csv(filename, sep=',')
        for filename in ssc_core_descriptive_filenames
    ]

    measure_df = pd.concat(measures_df)
    assert measure_df is not None
    return measure_df


def build_role(row):
    person_id = row['personId']
    [_fid, role] = person_id.split('.')
    if role == 'mo':
        return Role.mom
    elif role == 'fa':
        return Role.dad
    elif role[0] == 'p':
        return Role.prb
    elif role[0] == 's':
        return Role.sib
    else:
        print("Unknown role: {}".format(role))
        return None


def infer_roles(persons_df):
    roles = pd.Series("none", index=persons_df.index)
    statuses = pd.Series(Status.unaffected.value, index=persons_df.index)
    for index, row in persons_df.iterrows():
        role = build_role(row)
        roles[index] = role.name
        if role == Role.prb:
            statuses[index] = Status.affected.value

    persons_df['role'] = roles
    persons_df['status'] = statuses
    return persons_df


def build_sex(row):
    role = row['role']
    if role == Role.mom:
        return Sex.female
    elif role == Role.dad:
        return Sex.male
    elif row['sex_core'] == 'female':
        return Sex.female
    elif row['sex_core'] == 'male':
        return Sex.male
    elif row['sex'] == 'female':
        return Sex.female
    elif row['sex'] == 'male':
        return Sex.male
    elif row['sexI'] == 'F':
        return Sex.female
    elif row['sexI'] == 'M':
        return Sex.male
    else:
        return None


def infer_sex(persons_df, without_sex=[]):
    sex = pd.Series(0, index=persons_df.index, dtype=np.int32)
    for index, row in persons_df.iterrows():
        sex = build_sex(row)
        if sex is None:
            without_sex.append(row['personId'])
            sex[index] = 0
        else:
            sex[index] = sex.value
    persons_df['sex'] = sex

    return persons_df[persons_df.sex != 0]


def infer_race(persons_df):
    commonly_used_df = load_instrument('ssc_commonly_used')
    commonly_used_df = commonly_used_df.rename(
        columns={"individual": "personId"})
    assert 'personId' in commonly_used_df.columns
    commonly_used_df.set_index('personId', inplace=True)
    persons_df = persons_df.join(
        commonly_used_df, on='personId',
        rsuffix="_commonly_used")
    return persons_df


COLUMNS = [
    'familyId',
    'personId',
    'dadId',
    'momId',
    'sex',
    'status',
    'sampleId',
    'role',
    'birth',
    'age_at_assessment',
    'ssc_diagnosis_nonverbal_iq',
    'ssc_diagnosis_verbal_iq',
    'race',
    'race_parents',
]


def isnan(val):
    if isinstance(val, float) and np.isnan(val):
        return True
    return False


def build_race(race, race1, race2):
    if race1 == race2:
        return race1
    if race1 is None or race2 is None or \
            race1 == 'not-specified' or race2 == 'not-specified' or \
            race1 == '' or race2 == '' or \
            isnan(race1) or isnan(race2):
        if race:
            return race
        return 'not-specified'

    return 'more-than-one-race'


def build_pedigree(persons_df):
    assert 'familyId' in persons_df.columns
    moms = pd.Series("0", index=persons_df.index)
    dads = pd.Series("0", index=persons_df.index)
    samples = pd.Series("", index=persons_df.index)
    persons_df['momId'] = moms
    persons_df['dadId'] = dads
    persons_df['sampleId'] = samples

    persons_df = persons_df[COLUMNS]

    def find_mom_or_dad(family_df, role):
        df = family_df[family_df.role == role]
        assert len(df) <= 1
        if len(df) == 0:
            return "0"
        row = df.iloc[0]
        return row

    result = []
    grouped = persons_df.groupby('familyId')
    for _, family_df in grouped:
        mom = find_mom_or_dad(family_df, Role.mom.name)
        dad = find_mom_or_dad(family_df, Role.dad.name)

        family = []
        for _index, row in family_df.iterrows():
            person = {
                k: row[k] for k in list(row.keys())
            }

            if row.role not in set([Role.mom.name, Role.dad.name]):
                person['momId'] = mom.personId
                person['dadId'] = dad.personId
                person['race'] = build_race(
                    row.race,
                    mom.race_parents, dad.race_parents)
            elif row.role == Role.mom.name:
                person['race'] = mom.race_parents
            elif row.role == Role.dad.name:
                person['race'] = dad.race_parents

            family.append(person)
        result.extend(family)

    ped_df = pd.DataFrame(
        data=result,
        columns=COLUMNS,
    )
    return ped_df


def build_pedigree_file():
    persons_df = load_and_join()
    persons_df = infer_roles(persons_df)
    without_sex = []
    persons_df = infer_sex(persons_df, without_sex)
    persons_df = infer_race(persons_df)

    return build_pedigree(persons_df)


def main():
    ped_df = build_pedigree_file()
    ped_df.to_csv('ssc_v15.ped', index=False, sep='\t')


if __name__ == '__main__':
    main()
