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
            'measure_type': 'continuous',
            'measure': 'pheno_common.verbal_iq',
            'role': 'prb',
            'mmin': 10,
            'mmax': 20
        }
    ]
    res = ssc.get_family_filters(**query)
    assert len(res) == 1

    assert len(res[0]) == 120


def test_head_circumference_interval(ssc):
    query = copy.deepcopy(EXAMPLE_QUERY_SSC)
    query['phenoFilters'] = [
        {
            'measure_type': 'continuous',
            'measure': 'ssc_commonly_used.head_circumference',
            'role': 'prb',
            'mmin': 49,
            'mmax': 50
        }
    ]
    res = ssc.get_family_filters(**query)
    assert len(res) == 1

    assert len(res[0]) == 102


def test_categorical_measure_filter_race_hawaiian(ssc):
    query = copy.deepcopy(EXAMPLE_QUERY_SSC)
    query['phenoFilters'] = [
        {
            'measure_type': 'categorical',
            'measure': 'pheno_common.race',
            'role': 'prb',
            'selection': ['native-hawaiian'],
        }
    ]
    res = ssc.get_family_filters(**query)
    assert len(res) == 1
    assert len(res[0]) == 11


def test_categorical_measure_filter_race_native_american(ssc):
    query = copy.deepcopy(EXAMPLE_QUERY_SSC)
    query['phenoFilters'] = [
        {
            'measure_type': 'categorical',
            'measure': 'pheno_common.race',
            'role': 'prb',
            'selection': ['native-american'],
        }
    ]
    res = ssc.get_family_filters(**query)
    assert len(res) == 1
    assert len(res[0]) == 9
