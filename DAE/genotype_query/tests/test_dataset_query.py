'''
Created on Feb 6, 2017

@author: lubo
'''
import pytest
import copy
from pprint import pprint


EXAMPLE_QUERY_SSC = {
    "effect_types": "Frame-shift,Nonsense,Splice-site",
    "gender": "female,male",
    "present_in_child": "autism and unaffected,autism only",
    "present_in_parent": "neither",
    "variant_types": "CNV,del,ins,sub",
    "genes": "All",
    "family_race": "All",
    "family_quad_trio": "All",
    "family_prb_gender": "All",
    "family_sib_gender": "All",
    "family_study_type": "All",
    "family_studies": "All",
    "family_pheno_measure_min": 1.08,
    "family_pheno_measure_max": 40,
    "family_pheno_measure": "abc.subscale_ii_lethargy",
    "dataset_id": "SSC",
    "pedigree_selector": "phenotypes"
}

EXAMPLE_QUERY_VIP = {
    "effect_types": "Frame-shift,Nonsense,Splice-site",
    "gender": "female,male",
    "present_in_child": "autism and unaffected,autism only",
    "present_in_parent": "neither",
    "variant_types": "CNV,del,ins,sub",
    "genes": "All",
    "dataset_id": "VIP",
    "pedigree_selector": "16pstatus"
}


def test_none_dataset_id(query):
    with pytest.raises(AssertionError):
        query.get_variants(dataset_id=None)


def test_bad_dataset_id(query):
    with pytest.raises(AssertionError):
        query.get_variants(dataset_id='blah')


def test_good_dataset_id(query):
    query.get_variants(dataset_id='SSC')


def test_example_query(query):
    query.get_variants(**EXAMPLE_QUERY_SSC)
    query.get_legend(**EXAMPLE_QUERY_SSC)


def test_get_legend_ssc(query):
    legend = query.get_legend(**EXAMPLE_QUERY_SSC)
    assert legend is not None
    pprint(legend)
    assert 'name' in legend
    assert 'values' in legend

    assert 3 == len(legend['values'])


def test_get_legend_vip(query):
    legend = query.get_legend(**EXAMPLE_QUERY_VIP)
    assert legend is not None
    pprint(legend)
    assert 'name' in legend
    assert 'values' in legend

    assert 5 == len(legend['values'])


def test_get_legend_bad_pedigree(query):
    kwargs = copy.deepcopy(EXAMPLE_QUERY_SSC)
    kwargs['pedigree_selector'] = 'ala bala'
    with pytest.raises(AssertionError):
        query.get_legend(**kwargs)
