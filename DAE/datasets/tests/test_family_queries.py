'''
Created on Mar 3, 2017

@author: lubo
'''
import numpy as np

import copy
from datasets.tests.requests import EXAMPLE_QUERY_SSC
from pheno.common import Role


def test_verbal_iq_interval_ssc(ssc, ssc_pheno):
    fd = ssc
    assert fd is not None

    measure_id = 'ssc_core_descriptive.ssc_diagnosis_verbal_iq'
    family_ids = fd.get_families_by_measure_continuous(
        measure_id, 10, 11, roles=[Role.prb])
    assert family_ids is not None

    assert 15 == len(family_ids)

    df = ssc_pheno.get_persons_values_df(
        [measure_id], roles=[Role.prb])
    df.dropna(inplace=True)

    res = df[df.family_id.isin(set(family_ids))]
    print(res[res[measure_id] > 20])
    print(res[res.family_id.isin(set(['13143', '13593', '14683']))])

    assert np.all(res[measure_id] >= 10)
    assert np.all(res[measure_id] <= 11)


def test_head_circumference_interval(ssc, ssc_pheno):
    fd = ssc
    assert fd is not None

    family_ids = fd.get_families_by_measure_continuous(
        'ssc_commonly_used.head_circumference', 49, 50, roles=[Role.prb])
    assert family_ids is not None
    # assert 102 == len(family_ids)

    df = ssc_pheno.get_persons_values_df(
        ['ssc_commonly_used.head_circumference'], roles=[Role.prb])
    df.dropna(inplace=True)

    res = df[np.logical_and(
        df['ssc_commonly_used.head_circumference'] >= 49,
        df['ssc_commonly_used.head_circumference'] <= 50)]
    fams = res.family_id.unique()
    assert 102 == len(fams)
    assert 102 == len(family_ids)


def test_experiment_with_categorical_measure_filter(ssc, ssc_pheno):
    fd = ssc
    assert fd is not None

    family_ids = fd.get_families_by_measure_categorical(
        'pheno_common.race', ['native-hawaiian'])
    assert 11 == len(family_ids)

    family_ids = fd.get_families_by_measure_categorical(
        'pheno_common.race', ['native-american'])
    assert 9 == len(family_ids)

    family_ids = fd.get_families_by_measure_categorical(
        'pheno_common.race', ['native-hawaiian', 'native-american'])
    assert 20 == len(family_ids)


def test_family_ids_simple_denovo(ssc):
    query = copy.deepcopy(EXAMPLE_QUERY_SSC)
    query['familyIds'] = ['11563']
    del query['pedigreeSelector']

    vs = ssc.get_variants(**query)
    count = 0
    for v in vs:
        count += 1
        assert v.familyId == '11563'

    assert 1 == count


def test_family_ids_simple_transmitted(ssc):
    query = copy.deepcopy(EXAMPLE_QUERY_SSC)
    query['familyIds'] = ['11563']
    query['presentInParent'] = ['mother only']
    query['rarity'] = {'ultraRare': 'true'}

    del query['pedigreeSelector']

    vs = ssc.get_variants(**query)
    count = 0
    for v in vs:
        count += 1
        assert v.familyId == '11563'

    assert 1 == count
