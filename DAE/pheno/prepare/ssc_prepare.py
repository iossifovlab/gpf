'''
Created on Sep 18, 2017

@author: lubo
'''
import os

import pandas as pd


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
    individuals_v14_age_of_assessment_filename = os.path.join(
        data_dev_dir,
        'pheno/14',
        'ssc_age_at_assessment.csv')
    persons_df = pd.read_csv(individuals_v15_filename, sep='\t')
    persons_df = persons_df.rename(columns={"SSC ID": "personId"})
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

    persons_df = persons_df.join(persons_14_df, on='personId')
    persons_df = persons_df.join(persons_14_age_df, on='personId')

    measure_df = load_core_descriptive()
    measure_df = measure_df.rename(columns={'individual': 'personId'})
    measure_df.set_index('personId', inplace=True)

    persons_df = persons_df.join(measure_df, on='personId', rsuffix="_core")
    print(persons_df.columns)

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


def build_pedigree_file():
    persons_df = load_and_join()

    return persons_df
