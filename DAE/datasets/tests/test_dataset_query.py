'''
Created on Feb 6, 2017

@author: lubo
'''
import pytest
import copy
from pprint import pprint
from DAE import vDB


EXAMPLE_QUERY_SSC = {
    "effectTypes": "Frame-shift,Nonsense,Splice-site",
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
    "datasetId": "SSC",
    "pedigreeSelector": "phenotype"
}

EXAMPLE_QUERY_VIP = {
    "effectTypes": "Frame-shift,Nonsense,Splice-site",
    "gender": "female,male",
    "present_in_child": "autism and unaffected,autism only",
    "present_in_parent": "neither",
    "variant_types": "CNV,del,ins,sub",
    "genes": "All",
    "datasetId": "VIP",
    "pedigreeSelector": "16pstatus"
}

EXAMPLE_QUERY_SD = {
    "effectTypes": "Frame-shift,Nonsense,Splice-site",
    "gender": "female,male",
    "present_in_child": "autism and unaffected,autism only",
    "present_in_parent": "neither",
    "variant_types": "CNV,del,ins,sub",
    "genes": "All",
    "datasetId": "SD",
    "pedigreeSelector": "phenotype"
}


def test_example_query(query, datasets_config):
    dataset_descriptor = datasets_config.get_dataset(
        EXAMPLE_QUERY_SSC['datasetId'])
    query.get_variants(dataset_descriptor, **EXAMPLE_QUERY_SSC)

    query.get_legend(dataset_descriptor, **EXAMPLE_QUERY_SSC)


def test_get_legend_ssc(query, datasets_config):
    dataset_descriptor = datasets_config.get_dataset(
        EXAMPLE_QUERY_SSC['datasetId'])
    legend = query.get_legend(dataset_descriptor)
    assert legend is not None
    pprint(legend)
    assert 'name' in legend
    assert 'values' in legend

    assert 2 == len(legend['values'])


def test_get_legend_vip(query, datasets_config):
    dataset_descriptor = datasets_config.get_dataset(
        EXAMPLE_QUERY_VIP['datasetId'])
    legend = query.get_legend(dataset_descriptor)
    assert legend is not None
    pprint(legend)
    assert 'name' in legend
    assert 'values' in legend

    assert 4 == len(legend['values'])


def test_get_legend_bad_pedigree(query, datasets_config):
    dataset_descriptor = datasets_config.get_dataset(
        EXAMPLE_QUERY_SSC['datasetId'])

    kwargs = copy.deepcopy(EXAMPLE_QUERY_SSC)

    kwargs['pedigreeSelector'] = 'ala bala'
    with pytest.raises(AssertionError):
        query.get_legend(dataset_descriptor, **kwargs)


def test_get_effect_types(query):
    res = query.get_effect_types(**EXAMPLE_QUERY_SSC)
    assert res is not None

    assert set(['frame-shift', 'nonsense', 'splice-site']) == set(res)


def test_get_denovo_studies(query, datasets_config):
    dataset_descriptor = datasets_config.get_dataset(
        EXAMPLE_QUERY_SD['datasetId'])

    denovo = query.get_denovo_studies(dataset_descriptor, **EXAMPLE_QUERY_SSC)

    assert denovo is not None
    print([st.name for st in denovo])
    assert all([st.has_denovo for st in denovo])

    st = vDB.get_study('w1202s766e611')

    assert not st.has_denovo
    print(st.has_denovo)


def test_get_transmitted_stuides(query, datasets_config):
    dataset_descriptor = datasets_config.get_dataset(
        EXAMPLE_QUERY_SSC['datasetId'])

    transmitted = query.get_transmitted_studies(
        dataset_descriptor, **EXAMPLE_QUERY_SSC)
    assert transmitted

    assert all([st.has_transmitted for st in transmitted])


def test_get_denovo_variants_ssc(query, datasets_config):
    dataset_descriptor = datasets_config.get_dataset(
        EXAMPLE_QUERY_SSC['datasetId'])

    vs = query.get_denovo_variants(dataset_descriptor, **EXAMPLE_QUERY_SSC)
    res = [v for v in vs]
    assert 634 == len(res)


def test_get_denovo_variants_vip(query, datasets_config):
    dataset_descriptor = datasets_config.get_dataset(
        EXAMPLE_QUERY_VIP['datasetId'])
    vs = query.get_denovo_variants(dataset_descriptor, **EXAMPLE_QUERY_VIP)
    res = [v for v in vs]
    assert 64 == len(res)


def test_denovo_studies_persons_phenotype_ssc(query, datasets_config):
    dataset_descriptor = datasets_config.get_dataset(
        EXAMPLE_QUERY_SD['datasetId'])
    studies = query.get_denovo_studies(
        dataset_descriptor=dataset_descriptor, **EXAMPLE_QUERY_SSC)
    for st in studies:
        phenotype = st.get_attr('study.phenotype')
        for fam in st.families.values():
            for p in fam.memberInOrder:
                if p.role == 'prb':
                    assert p.phenotype == phenotype
                else:
                    assert p.phenotype == 'unaffected'


def test_denovo_studies_persons_phenotype_sd(query, datasets_config):
    dataset_descriptor = datasets_config.get_dataset(
        EXAMPLE_QUERY_SD['datasetId'])

    studies = query.get_denovo_studies(
        dataset_descriptor=dataset_descriptor, **EXAMPLE_QUERY_SD)

    for st in studies:
        phenotype = st.get_attr('study.phenotype')
        print(phenotype)
        for fam in st.families.values():
            for p in fam.memberInOrder:
                if p.role == 'prb':
                    assert p.phenotype == phenotype
                else:
                    assert p.phenotype == 'unaffected'
