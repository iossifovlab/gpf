'''
Created on Mar 25, 2017

@author: lubo
'''
import copy
from datasets.tests.requests import EXAMPLE_QUERY_SSC


def test_verbal_iq_interval_ssc(ssc):
    query = copy.deepcopy(EXAMPLE_QUERY_SSC)
    query['phenoFilters'] = [
        {
            'measureType': 'continuous',
            'measure': 'pheno_common.verbal_iq',
            'role': 'prb',
            'mmin': 10,
            'mmax': 20
        }
    ]
    res = ssc.get_family_pheno_filters(**query)
    assert len(res) == 1

    assert len(res[0]) == 120


def test_head_circumference_interval(ssc):
    query = copy.deepcopy(EXAMPLE_QUERY_SSC)
    query['phenoFilters'] = [
        {
            'measureType': 'continuous',
            'measure': 'ssc_commonly_used.head_circumference',
            'role': 'prb',
            'mmin': 49,
            'mmax': 50
        }
    ]
    res = ssc.get_family_pheno_filters(**query)
    assert len(res) == 1

    assert len(res[0]) == 102


def test_categorical_measure_filter_race_hawaiian(ssc):
    query = copy.deepcopy(EXAMPLE_QUERY_SSC)
    query['phenoFilters'] = [
        {
            'measureType': 'categorical',
            'measure': 'pheno_common.race',
            'role': 'prb',
            'selection': ['native-hawaiian'],
        }
    ]
    res = ssc.get_family_pheno_filters(**query)
    assert len(res) == 1
    assert len(res[0]) == 11


def test_categorical_measure_filter_race_native_american(ssc):
    query = copy.deepcopy(EXAMPLE_QUERY_SSC)
    query['phenoFilters'] = [
        {
            'measureType': 'categorical',
            'measure': 'pheno_common.race',
            'role': 'prb',
            'selection': ['native-american'],
        }
    ]
    res = ssc.get_family_pheno_filters(**query)
    assert len(res) == 1
    assert len(res[0]) == 9


def test_head_circumference_interval_variants(ssc):
    query = copy.deepcopy(EXAMPLE_QUERY_SSC)
    query['phenoFilters'] = [
        {
            'measureType': 'continuous',
            'measure': 'ssc_commonly_used.head_circumference',
            'role': 'prb',
            'mmin': 49,
            'mmax': 50
        }
    ]
    vs = ssc.get_variants(**query)
    assert vs is not None

    assert 19 == len(list(vs))


def test_categorical_measure_filter_race_hawaiian_variants(ssc):
    query = copy.deepcopy(EXAMPLE_QUERY_SSC)
    query['phenoFilters'] = [
        {
            'measureType': 'categorical',
            'measure': 'pheno_common.race',
            'role': 'prb',
            'selection': ['native-hawaiian'],
        }
    ]
    query['familyIds'] = ['11483']

    vs = ssc.get_variants(**query)
    vs = list(vs)
    assert len(vs) == 1
    assert vs[0].familyId == '11483'


def test_pheno_filter_combine_variants(ssc):
    query = copy.deepcopy(EXAMPLE_QUERY_SSC)
    query['phenoFilters'] = [
        {
            'measureType': 'categorical',
            'measure': 'pheno_common.race',
            'role': 'prb',
            'selection': ['native-hawaiian'],
        },
        {
            'measureType': 'continuous',
            'measure': 'pheno_common.non_verbal_iq',
            'role': 'prb',
            'mmin': 80,
            'mmax': 80
        }
    ]

    vs = ssc.get_variants(**query)
    vs = list(vs)
    assert len(vs) == 1
    assert vs[0].familyId == '11483'


def test_pheno_filter_combine_variants_a2(ssc):
    query = copy.deepcopy(EXAMPLE_QUERY_SSC)
    query['phenoFilters'] = [
        {
            'measureType': 'categorical',
            'measure': 'pheno_common.race',
            'role': 'prb',
            'selection': ['native-hawaiian', 'white'],
        },
        {
            'measureType': 'continuous',
            'measure': 'pheno_common.non_verbal_iq',
            'role': 'prb',
            'mmin': 80,
            'mmax': 80
        }
    ]

    vs = ssc.get_variants(**query)
    vs = list(vs)
    assert len(vs) == 7
