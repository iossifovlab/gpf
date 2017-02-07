'''
Created on Feb 6, 2017

@author: lubo
'''
import pytest
import copy
from pprint import pprint
from DAE import vDB


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
    dataset = query.get_dataset(EXAMPLE_QUERY_SSC['dataset_id'])

    query.get_legend(dataset, **EXAMPLE_QUERY_SSC)


def test_get_legend_ssc(query):
    dataset = query.get_dataset(**EXAMPLE_QUERY_SSC)
    legend = query.get_legend(dataset)
    assert legend is not None
    pprint(legend)
    assert 'name' in legend
    assert 'values' in legend

    assert 3 == len(legend['values'])


def test_get_legend_vip(query):
    dataset = query.get_dataset(**EXAMPLE_QUERY_VIP)
    legend = query.get_legend(dataset)
    assert legend is not None
    pprint(legend)
    assert 'name' in legend
    assert 'values' in legend

    assert 5 == len(legend['values'])


def test_get_legend_bad_pedigree(query):
    dataset = query.get_dataset(**EXAMPLE_QUERY_SSC)
    kwargs = copy.deepcopy(EXAMPLE_QUERY_SSC)

    kwargs['pedigree_selector'] = 'ala bala'
    with pytest.raises(AssertionError):
        query.get_legend(dataset, **kwargs)


def test_get_effect_types(query):
    res = query.get_effect_types(**EXAMPLE_QUERY_SSC)
    assert res is not None

    assert set(['frame-shift', 'nonsense', 'splice-site']) == set(res)


def test_get_denovo_studies(query):
    dataset = query.get_dataset(**EXAMPLE_QUERY_SSC)
    denovo = query.get_denovo_studies(dataset, **EXAMPLE_QUERY_SSC)

    assert denovo is not None
    print([st.name for st in denovo])
    assert all([st.has_denovo for st in denovo])

    st = vDB.get_study('w1202s766e611')

    assert not st.has_denovo
    print(st.has_denovo)


def test_get_transmitted_stuides(query):
    dataset = query.get_dataset(**EXAMPLE_QUERY_SSC)
    transmitted = query.get_transmitted_studies(dataset, **EXAMPLE_QUERY_SSC)
    assert transmitted

    assert all([st.has_transmitted for st in transmitted])
