'''
Created on Sep 18, 2017

@author: lubo
'''
import os

import pandas as pd
from pheno.common import Role, Gender


def load_and_join():
    data_dev_dir = os.environ['DAE_DB_DIR']
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
            'gender': 'genderI',
            'role': 'roleI'
        })
    assert 'personId' in individuals_df.columns
    print(individuals_df.head())

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

    measure_df = load_core_descriptive()
    measure_df = measure_df.rename(columns={'individual': 'personId'})
    measure_df.set_index('personId', inplace=True)

    persons_df = persons_df.join(measure_df, on='personId', rsuffix="_core")

    print(persons_df.columns)
    print(persons_df[['personId', 'familyId', 'family']].head())

    return persons_df


def load_core_descriptive():
    data_dev_dir = os.environ['DAE_DB_DIR']
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
            'ssc_core_descriptive.csv'
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
    for index, row in persons_df.iterrows():
        roles[index] = build_role(row)
    persons_df['role'] = roles

    return persons_df


def build_gender(row):
    role = row['role']
    if role == Role.mom:
        return Gender.F
    elif role == Role.dad:
        return Gender.M
    elif row['sex_core'] == 'female':
        return Gender.F
    elif row['sex_core'] == 'male':
        return Gender.M
    elif row['sex'] == 'female':
        return Gender.F
    elif row['sex'] == 'male':
        return Gender.M
    elif row['genderI'] == 'F':
        return Gender.F
    elif row['genderI'] == 'M':
        return Gender.M
    else:
        return None


def infer_gender(persons_df, without_gender=[]):
    gender = pd.Series("none", index=persons_df.index)
    for index, row in persons_df.iterrows():
        sex = build_gender(row)
        if sex is None:
            without_gender.append(row['personId'])
        gender[index] = sex
    persons_df['gender'] = gender
    return persons_df


def build_pedigree(persons_df):
    assert 'familyId' in persons_df.columns
    moms = pd.Series("0", index=persons_df.index)
    dads = pd.Series("0", index=persons_df.index)
    persons_df['momId'] = moms
    persons_df['dadId'] = dads

    persons_df = persons_df[[
        'familyId',
        'personId',
        'dadId',
        'momId',
        'gender',
        # 'status',
        'role',
    ]]

    def find_mom_or_dad(family_df, role):
        df = family_df[family_df.role == role]
        assert len(df) <= 1
        if len(df) == 0:
            return "0"
        row = df.iloc[0]
        return row.personId

    result = []
    grouped = persons_df.groupby('familyId')
    for _, family_df in grouped:
        mom = find_mom_or_dad(family_df, Role.mom)
        dad = find_mom_or_dad(family_df, Role.dad)
        for index, row in family_df.iterrows():
            if row.role not in set([Role.mom, Role.dad]):
                row.momId = mom
                row.dadId = dad
        result.append(family_df)

    if len(result) == 1:
        return result[0]
    else:
        return pd.concat(result)


def build_pedigree_file():
    persons_df = load_and_join()
    persons_df = infer_roles(persons_df)
    without_gender = []
    persons_df = infer_gender(persons_df, without_gender)
    return build_pedigree(persons_df)
