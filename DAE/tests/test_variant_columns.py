'''
Created on Sep 27, 2016

@author: lubo
'''
from query_variants import do_query_variants, dae_query_variants, augment_vars
import itertools


def test_dae_query():
    query = {
        'denovoStudies': 'ALL SSC',
        'geneRegion': 'chr5:140,117,933-140,900,259',
    }

    vs = dae_query_variants(query)

    for v in itertools.chain(*vs):
        print(v)
        print(getattr(v, 'geneEffect'))
        print(getattr(v, 'requestedGeneEffects'))


def test_do_query():
    query = {
        'denovoStudies': 'ALL SSC',
        'geneRegion': 'chr5:140,117,933-140,900,259',
    }

    vs = do_query_variants(query)

    for v in vs:
        print(v)


def test_variant_phenotype_augment_attribute():
    query = {
        'denovoStudies': 'ALL SSC',
        'geneRegion': 'chr5:140,117,933-140,900,259',
    }

    vs = dae_query_variants(query)

    for v in itertools.chain(*vs):
        v = augment_vars(v)
        print(v.atts)
        assert '_phenotype_' in v.atts
        assert 'autism' == v.atts['_phenotype_']
        assert 'autism' == getattr(v, '_phenotype_')
