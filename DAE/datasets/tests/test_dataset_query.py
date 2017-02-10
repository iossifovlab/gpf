'''
Created on Feb 6, 2017

@author: lubo
'''
import pytest
import copy
from pprint import pprint
from DAE import vDB
from datasets.tests.requests import EXAMPLE_QUERY_SSC, EXAMPLE_QUERY_VIP


def test_get_legend_ssc(ssc):
    legend = ssc.get_pedigree_selector(**EXAMPLE_QUERY_SSC)
    assert legend is not None
    pprint(legend)
    assert 'name' in legend
    assert 'values' in legend

    assert 2 == len(legend['values'])


def test_get_legend_vip(vip):
    legend = vip.get_pedigree_selector(**EXAMPLE_QUERY_VIP)
    assert legend is not None
    pprint(legend)
    assert 'name' in legend
    assert 'values' in legend

    assert 4 == len(legend['values'])


def test_get_legend_bad_pedigree(ssc):
    kwargs = copy.deepcopy(EXAMPLE_QUERY_SSC)

    kwargs['pedigreeSelector'] = 'ala bala'
    with pytest.raises(AssertionError):
        ssc.get_pedigree_selector(**kwargs)


def test_get_effect_types(ssc):
    res = ssc.get_effect_types(**EXAMPLE_QUERY_SSC)
    assert res is not None

    assert set(['frame-shift', 'nonsense', 'splice-site']) == set(res)


def test_get_denovo_studies(sd):
    denovo = sd.denovo_studies

    assert denovo is not None
    print([st.name for st in denovo])
    assert all([st.has_denovo for st in denovo])

    st = vDB.get_study('w1202s766e611')

    assert not st.has_denovo
    print(st.has_denovo)


def test_get_transmitted_stuides(ssc):
    transmitted = ssc.transmitted_studies
    assert transmitted

    assert all([st.has_transmitted for st in transmitted])


def test_get_denovo_variants_ssc(ssc):
    vs = ssc.get_denovo_variants(**EXAMPLE_QUERY_SSC)
    res = [v for v in vs]
    assert 422 == len(res)


def test_get_denovo_variants_vip(vip):
    vs = vip.get_denovo_variants(**EXAMPLE_QUERY_VIP)
    res = [v for v in vs]
    assert 18 == len(res)


def test_denovo_studies_persons_phenotype_ssc(ssc):
    studies = ssc.denovo_studies
    for st in studies:
        phenotype = st.get_attr('study.phenotype')
        for fam in st.families.values():
            for p in fam.memberInOrder:
                if p.role == 'prb':
                    assert p.phenotype == phenotype
                else:
                    assert p.phenotype == 'unaffected'


def test_denovo_studies_persons_phenotype_sd(sd):
    for st in sd.denovo_studies:
        phenotype = st.get_attr('study.phenotype')
        print(phenotype)
        for fam in st.families.values():
            for p in fam.memberInOrder:
                if p.role == 'prb':
                    assert p.phenotype == phenotype
                else:
                    assert p.phenotype == 'unaffected'
