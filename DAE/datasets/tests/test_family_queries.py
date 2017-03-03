'''
Created on Mar 3, 2017

@author: lubo
'''
import pytest
import numpy as np

import DAE
from datasets.phenotype_base import SSCFamilyQueryDelegate


@pytest.fixture(scope='session')
def ssc_pheno(request):
    pf = DAE.pheno
    db = pf.get_pheno_db('ssc')
    return db


def test_verbal_iq_interval_ssc(ssc, ssc_pheno):
    fd = SSCFamilyQueryDelegate(ssc)
    assert fd is not None

    family_ids = fd.get_families_by_measure_continuous(
        'pheno_common.verbal_iq', 10, 20, roles=['prb'])
    assert family_ids is not None

    assert 120 == len(family_ids)

    df = ssc_pheno.get_persons_values_df(
        ['pheno_common.verbal_iq'], roles=['prb'])
    df.dropna(inplace=True)

    res = df[df.family_id.isin(set(family_ids))]
    assert np.all(res['pheno_common.verbal_iq'] >= 10)
    assert np.all(res['pheno_common.verbal_iq'] <= 20)


def test_head_circumference_interval(ssc, ssc_pheno):
    fd = SSCFamilyQueryDelegate(ssc)
    assert fd is not None

    family_ids = fd.get_families_by_measure_continuous(
        'ssc_commonly_used.head_circumference', 49, 50, roles=['prb'])
    assert family_ids is not None
    # assert 102 == len(family_ids)

    df = ssc_pheno.get_persons_values_df(
        ['ssc_commonly_used.head_circumference'], roles=['prb'])
    df.dropna(inplace=True)

    res = df[np.logical_and(
        df['ssc_commonly_used.head_circumference'] >= 49,
        df['ssc_commonly_used.head_circumference'] <= 50)]
    fams = res.family_id.unique()
    assert 102 == len(fams)
    assert 102 == len(family_ids)


def test_experiment_with_categorical_measure_filter(ssc, ssc_pheno):
    fd = SSCFamilyQueryDelegate(ssc)
    assert fd is not None

    domain = fd.get_measure_domain_categorical('pheno_common.race')
    print(domain)

    family_ids = fd.get_families_by_measure_categorical(
        'pheno_common.race', ['native-hawaiian'])
    assert 11 == len(family_ids)

    family_ids = fd.get_families_by_measure_categorical(
        'pheno_common.race', ['native-american'])
    assert 9 == len(family_ids)

    family_ids = fd.get_families_by_measure_categorical(
        'pheno_common.race', ['native-hawaiian', 'native-american'])
    assert 20 == len(family_ids)
